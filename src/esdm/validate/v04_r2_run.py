"""Replicated outcome runner for the frozen v0.4-R2 hard separation gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_gate import (
    R2_RECOVERY_TRUTH,
    V04R2Summary,
    evaluate_v04_r2_identification_profiles,
)
from .v04_r2_state_activity import build_v04_r2_fixture


_STATE_BLOCKS = (
    ("annotated.sp.resting", "resting"),
    ("annotated.sp.foraging", "foraging"),
)


@dataclass(frozen=True, slots=True)
class V04R2Replicate:
    replicate: int
    posterior_means: Mapping[str, float]
    posterior_lows: Mapping[str, float]
    posterior_highs: Mapping[str, float]
    full_heldout_log_score: float
    activity_knockout_heldout_log_score: float
    state_knockout_heldout_log_score: float
    full_divergences: int
    activity_knockout_divergences: int
    state_knockout_divergences: int

    def __post_init__(self) -> None:
        expected = set(R2_RECOVERY_TRUTH)
        cleaned = {}
        for name, source in (
            ("posterior_means", self.posterior_means),
            ("posterior_lows", self.posterior_lows),
            ("posterior_highs", self.posterior_highs),
        ):
            values = {str(key): float(value) for key, value in source.items()}
            if set(values) != expected:
                raise ValueError(
                    f"{name} targets must match frozen R2 recovery targets"
                )
            cleaned[name] = MappingProxyType(values)
        for name, values in cleaned.items():
            object.__setattr__(self, name, values)

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

    def covers_truth(self, target: str) -> bool:
        truth = float(R2_RECOVERY_TRUTH[target])
        return (
            self.posterior_lows[target]
            <= truth
            <= self.posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V04R2Result:
    replicates: tuple[V04R2Replicate, ...]
    summary: V04R2Summary
    train_space_count: int
    heldout_space_count: int
    calibration_space_count: int


def _quantile(values, probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("posterior draws must be non-empty")
    p = float(probability)
    if not 0.0 <= p <= 1.0:
        raise ValueError("quantile probability must be in [0, 1]")
    if len(ordered) == 1:
        return ordered[0]
    position = p * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _subset_model(fixture, spaces, *, knockout: str | None):
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


def _subset_data(generated_counts, model: Model):
    ordered_keys = tuple(model.domain.keys)
    output = {}
    for stream in model.streams:
        output[stream.name] = {}
        for species in model.stream_targets(stream):
            source = generated_counts[stream.name][species]
            state_space = getattr(stream, "state_space", None)
            if state_space is None:
                output[stream.name][species] = {
                    key: int(source[key])
                    for key in ordered_keys
                }
                continue
            output[stream.name][species] = {
                state: {
                    key: int(source[state][key])
                    for key in ordered_keys
                }
                for state in state_space.states
            }
    return output


def _logmeanexp(values) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("logmeanexp needs at least one value")
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


def _state_block_log_predictive_density(
    model,
    samples,
    covariates,
    data,
) -> float:
    """Mean posterior Poisson LPD over both annotated state blocks and contexts."""

    from esdm.model.backend_numpyro import posterior_observation_rates

    if (
        "annotated" not in data
        or "sp" not in data["annotated"]
    ):
        raise KeyError("missing held-out annotated data for sp")
    counts_by_state = data["annotated"]["sp"]
    rates_by_block = posterior_observation_rates(
        model,
        samples,
        covariates,
    )
    ordered_keys = tuple(model.domain.keys)
    scores = []
    for block_name, state in _STATE_BLOCKS:
        if block_name not in rates_by_block:
            raise KeyError(
                f"posterior observation rates missing block {block_name!r}"
            )
        if state not in counts_by_state:
            raise KeyError(f"missing held-out annotated state {state!r}")
        draws = tuple(rates_by_block[block_name])
        if not draws:
            raise ValueError("posterior block rates require at least one draw")
        if any(len(draw) != len(ordered_keys) for draw in draws):
            raise ValueError("posterior block rates do not match held-out domain")
        counts_map = counts_by_state[state]
        unknown = set(counts_map) - set(ordered_keys)
        if unknown:
            raise ValueError("held-out state counts contain contexts outside domain")
        counts = tuple(int(counts_map.get(key, 0)) for key in ordered_keys)
        if any(value < 0 for value in counts):
            raise ValueError("held-out state counts must be non-negative")
        for index, count in enumerate(counts):
            scores.append(
                _logmeanexp(
                    _poisson_log_mass(count, draw[index])
                    for draw in draws
                )
            )
    if not scores:
        raise ValueError("held-out state scoring requires observations")
    return math.fsum(scores) / len(scores)


def _posterior_intervals(samples, alpha: float):
    means = {}
    lows = {}
    highs = {}
    for site in R2_RECOVERY_TRUTH:
        if site not in samples:
            raise KeyError(f"posterior samples missing recovery site {site!r}")
        draws = tuple(float(value) for value in samples[site])
        means[site] = math.fsum(draws) / len(draws)
        lows[site] = _quantile(draws, alpha)
        highs[site] = _quantile(draws, 1.0 - alpha)
    return means, lows, highs


def _extrapolation_integrity(fixture) -> bool:
    doy = fixture.model.domain.doy[0]
    hour = fixture.model.domain.hour[0]
    train_max = max(
        fixture.covariates[(space, doy, hour)]["eastness_z_train"]
        for space in fixture.train_spaces
    )
    heldout_min = min(
        fixture.covariates[(space, doy, hour)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    )
    return heldout_min > train_max


def summarize_v04_r2(
    records: Sequence[V04R2Replicate],
    *,
    identification,
    extrapolation_integrity: bool,
) -> V04R2Summary:
    rows = tuple(records)
    if not rows:
        raise ValueError("R2 validation records must be non-empty")
    n = len(rows)
    mean_biases = {}
    coverages = {}
    for target, truth in R2_RECOVERY_TRUTH.items():
        mean_biases[target] = (
            math.fsum(
                row.posterior_means[target] - float(truth)
                for row in rows
            )
            / n
        )
        coverages[target] = (
            math.fsum(
                1.0 if row.covers_truth(target) else 0.0
                for row in rows
            )
            / n
        )
    return V04R2Summary(
        replicates=n,
        fit_count=3 * n,
        positive_structural_pass=identification.positive_structural_pass,
        positive_practical_pass=identification.positive_practical_pass,
        sparse_structural_pass=identification.sparse_structural_pass,
        sparse_practical_refused=identification.sparse_practical_refused,
        unknown_detection_refused=identification.unknown_detection_refused,
        extrapolation_integrity=bool(extrapolation_integrity),
        mean_biases=mean_biases,
        coverages=coverages,
        activity_positive_gain_rate=(
            math.fsum(1.0 if row.activity_gain > 0.0 else 0.0 for row in rows)
            / n
        ),
        mean_activity_gain=math.fsum(row.activity_gain for row in rows) / n,
        state_positive_gain_rate=(
            math.fsum(1.0 if row.state_gain > 0.0 else 0.0 for row in rows)
            / n
        ),
        mean_state_gain=math.fsum(row.state_gain for row in rows) / n,
        total_divergences=sum(
            int(row.full_divergences)
            + int(row.activity_knockout_divergences)
            + int(row.state_knockout_divergences)
            for row in rows
        ),
    )


def run_v04_r2_replicate(
    source_csv_text: str,
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04R2Replicate:
    """Run one frozen R2 positive-profile replicate."""

    from esdm.model.backend_numpyro import fit_numpyro

    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    alpha = (1.0 - mass) / 2.0
    fixture = build_v04_r2_fixture(
        source_csv_text,
        profile="positive",
    )

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

    generated = simulate_observations(
        fixture.model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_data = _subset_data(generated.counts, full_train)
    heldout_data = _subset_data(generated.counts, full_heldout)

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    full_fit = fit_numpyro(
        full_train,
        train_data,
        train_covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    activity_fit = fit_numpyro(
        activity_train,
        train_data,
        activity_train_covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )
    state_fit = fit_numpyro(
        state_train,
        train_data,
        state_train_covariates,
        rng_seed=int(seed) + 3,
        **fit_kwargs,
    )

    means, lows, highs = _posterior_intervals(full_fit.samples, alpha)
    full_score = _state_block_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_covariates,
        heldout_data,
    )
    activity_score = _state_block_log_predictive_density(
        activity_heldout,
        activity_fit.samples,
        activity_heldout_covariates,
        heldout_data,
    )
    state_score = _state_block_log_predictive_density(
        state_heldout,
        state_fit.samples,
        state_heldout_covariates,
        heldout_data,
    )
    return V04R2Replicate(
        replicate=int(replicate),
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_score,
        state_knockout_heldout_log_score=state_score,
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
    )


def run_v04_r2_benchmark(
    source_csv_text: str,
    *,
    replicates: int = 16,
    base_seed: int = 20260926,
    seed_stride: int = 47,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04R2Result:
    """Run the complete frozen R2 benchmark in the current process."""

    fixture = build_v04_r2_fixture(
        source_csv_text,
        profile="positive",
    )
    identification = evaluate_v04_r2_identification_profiles(source_csv_text)
    rows = tuple(
        run_v04_r2_replicate(
            source_csv_text,
            replicate=replicate,
            seed=int(base_seed) + replicate * int(seed_stride),
            num_warmup=num_warmup,
            num_samples=num_samples,
            num_chains=num_chains,
            credible_mass=credible_mass,
            progress_bar=progress_bar,
            target_accept_prob=target_accept_prob,
        )
        for replicate in range(int(replicates))
    )
    summary = summarize_v04_r2(
        rows,
        identification=identification,
        extrapolation_integrity=_extrapolation_integrity(fixture),
    )
    return V04R2Result(
        replicates=rows,
        summary=summary,
        train_space_count=len(fixture.train_spaces),
        heldout_space_count=len(fixture.heldout_spaces),
        calibration_space_count=len(fixture.calibration_spaces),
    )
