"""One-shot empirical R5b fitting/scoring for Snapshot Japan Camtrap DP."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping

from esdm.domain import Grid
from esdm.model import Model

from .empirical_snapshot_japan_camtrapdp import SnapshotJapanEmpiricalFixture


FROZEN_NUM_WARMUP = 300
FROZEN_NUM_SAMPLES = 350
FROZEN_NUM_CHAINS = 2
FROZEN_TARGET_ACCEPT = 0.90
FROZEN_CREDIBLE_MASS = 0.90


@dataclass(frozen=True, slots=True)
class EmpiricalR5BFitResult:
    parameter_summaries: Mapping[str, Mapping[str, float]]
    full_heldout_log_score: float
    activity_knockout_heldout_log_score: float
    state_knockout_heldout_log_score: float
    full_divergences: int
    activity_knockout_divergences: int
    state_knockout_divergences: int

    @property
    def activity_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.activity_knockout_heldout_log_score)
        )

    @property
    def state_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.state_knockout_heldout_log_score)
        )


def _subset_model(
    fixture: SnapshotJapanEmpiricalFixture,
    spaces,
    *,
    knockout: str | None,
):
    grid = Grid(
        space=tuple(str(space) for space in spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    if knockout is not None:
        if knockout not in {"activity", "state"}:
            raise ValueError("knockout must be None, 'activity', or 'state'")
        model = model.knockout("sp", knockout)
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def _subset_data(fixture: SnapshotJapanEmpiricalFixture, model: Model):
    keys = tuple(model.domain.keys)
    output = {}
    for stream in model.streams:
        output[stream.name] = {}
        for species in model.stream_targets(stream):
            source = fixture.data[stream.name][species]
            state_space = getattr(stream, "state_space", None)
            if state_space is None:
                output[stream.name][species] = {
                    key: int(source.get(key, 0))
                    for key in keys
                }
            else:
                output[stream.name][species] = {
                    state: {
                        key: int(source[state].get(key, 0))
                        for key in keys
                    }
                    for state in state_space.states
                }
    return output


def _logmeanexp(values) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("logmeanexp requires at least one draw")
    maximum = max(rows)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in rows)
        / len(rows)
    )


def _poisson_log_mass(count: int, rate: float) -> float:
    y = int(count)
    lam = float(rate)
    if y < 0 or not math.isfinite(lam) or lam < 0.0:
        raise ValueError("invalid Poisson count/rate")
    if lam == 0.0:
        return 0.0 if y == 0 else -math.inf
    return y * math.log(lam) - lam - math.lgamma(y + 1.0)


def _annotated_log_predictive_density(
    model,
    samples,
    covariates,
    data,
) -> float:
    from esdm.model.backend_numpyro import posterior_observation_rates

    counts_by_state = data["annotated"]["sp"]
    rates_by_block = posterior_observation_rates(
        model,
        samples,
        covariates,
    )
    ordered_keys = tuple(model.domain.keys)
    scores = []
    for state in ("solitary", "group"):
        block_name = f"annotated.sp.{state}"
        if block_name not in rates_by_block:
            raise KeyError(
                f"posterior observation rates missing {block_name!r}"
            )
        draws = tuple(rates_by_block[block_name])
        counts = tuple(
            int(counts_by_state[state].get(key, 0))
            for key in ordered_keys
        )
        for index, count in enumerate(counts):
            scores.append(
                _logmeanexp(
                    _poisson_log_mass(count, draw[index])
                    for draw in draws
                )
            )
    if not scores:
        raise ValueError("heldout annotated scoring has no contexts")
    return math.fsum(scores) / len(scores)


def _quantile(values, probability: float) -> float:
    rows = sorted(float(value) for value in values)
    if not rows:
        raise ValueError("posterior summary requires draws")
    p = float(probability)
    if len(rows) == 1:
        return rows[0]
    position = p * (len(rows) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return rows[lower]
    weight = position - lower
    return rows[lower] * (1.0 - weight) + rows[upper] * weight


def _parameter_summaries(samples):
    alpha = (1.0 - FROZEN_CREDIBLE_MASS) / 2.0
    output = {}
    for site, values in samples.items():
        name = str(site)
        if not (name.startswith("sp.") or name.startswith("stream.")):
            continue
        draws = tuple(float(value) for value in values)
        output[name] = {
            "mean": math.fsum(draws) / len(draws),
            "q05": _quantile(draws, alpha),
            "q95": _quantile(draws, 1.0 - alpha),
        }
    return output


def fit_snapshot_japan_empirical(
    fixture: SnapshotJapanEmpiricalFixture,
    *,
    rng_seed: int = 20260927,
    progress_bar: bool = False,
) -> EmpiricalR5BFitResult:
    """Fit the unchanged R5b full/activity-knockout/state-knockout endpoint."""

    from esdm.model.backend_numpyro import fit_numpyro

    full_train, train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout=None
    )
    activity_train, activity_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout="activity"
    )
    state_train, state_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout="state"
    )
    full_heldout, heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=None
    )
    activity_heldout, activity_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout="activity"
    )
    state_heldout, state_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout="state"
    )

    train_data = _subset_data(fixture, full_train)
    heldout_data = _subset_data(fixture, full_heldout)
    fit_kwargs = {
        "num_warmup": FROZEN_NUM_WARMUP,
        "num_samples": FROZEN_NUM_SAMPLES,
        "num_chains": FROZEN_NUM_CHAINS,
        "progress_bar": bool(progress_bar),
        "target_accept_prob": FROZEN_TARGET_ACCEPT,
    }
    full_fit = fit_numpyro(
        full_train,
        train_data,
        train_covariates,
        rng_seed=int(rng_seed),
        **fit_kwargs,
    )
    activity_fit = fit_numpyro(
        activity_train,
        train_data,
        activity_train_covariates,
        rng_seed=int(rng_seed) + 1,
        **fit_kwargs,
    )
    state_fit = fit_numpyro(
        state_train,
        train_data,
        state_train_covariates,
        rng_seed=int(rng_seed) + 2,
        **fit_kwargs,
    )

    return EmpiricalR5BFitResult(
        parameter_summaries=_parameter_summaries(full_fit.samples),
        full_heldout_log_score=_annotated_log_predictive_density(
            full_heldout,
            full_fit.samples,
            heldout_covariates,
            heldout_data,
        ),
        activity_knockout_heldout_log_score=_annotated_log_predictive_density(
            activity_heldout,
            activity_fit.samples,
            activity_heldout_covariates,
            heldout_data,
        ),
        state_knockout_heldout_log_score=_annotated_log_predictive_density(
            state_heldout,
            state_fit.samples,
            state_heldout_covariates,
            heldout_data,
        ),
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
    )
