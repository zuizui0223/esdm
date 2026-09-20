"""Replicated outcome runner for the already-frozen v0.4 state/activity gate."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .evidence import poisson_block_log_predictive_density
from .v04_state_activity import build_v04_state_activity_fixture
from .v04_state_activity_gate import (
    V04SemiSyntheticSummary,
    evaluate_v04_identification_profiles,
)


V04_STATE_BLOCKS = (
    "annotated.sp.resting",
    "annotated.sp.foraging",
)


@dataclass(frozen=True, slots=True)
class V04Replicate:
    replicate: int
    activity_beta_precip_mean: float
    activity_beta_precip_low: float
    activity_beta_precip_high: float
    activity_beta_eastness_mean: float
    activity_beta_eastness_low: float
    activity_beta_eastness_high: float
    state_beta_precip_mean: float
    state_beta_precip_low: float
    state_beta_precip_high: float
    state_beta_eastness_mean: float
    state_beta_eastness_low: float
    state_beta_eastness_high: float
    full_heldout_log_score: float
    activity_knockout_heldout_log_score: float
    state_knockout_heldout_log_score: float
    full_divergences: int
    activity_knockout_divergences: int
    state_knockout_divergences: int

    @property
    def activity_gain(self) -> float:
        return (
            self.full_heldout_log_score
            - self.activity_knockout_heldout_log_score
        )

    @property
    def state_gain(self) -> float:
        return (
            self.full_heldout_log_score
            - self.state_knockout_heldout_log_score
        )

    @property
    def activity_beta_precip_covers_truth(self) -> bool:
        return self.activity_beta_precip_low <= 0.55 <= self.activity_beta_precip_high

    @property
    def activity_beta_eastness_covers_truth(self) -> bool:
        return self.activity_beta_eastness_low <= 0.40 <= self.activity_beta_eastness_high

    @property
    def state_beta_precip_covers_truth(self) -> bool:
        return self.state_beta_precip_low <= -0.50 <= self.state_beta_precip_high

    @property
    def state_beta_eastness_covers_truth(self) -> bool:
        return self.state_beta_eastness_low <= 0.45 <= self.state_beta_eastness_high


@dataclass(frozen=True, slots=True)
class V04Result:
    replicates: tuple[V04Replicate, ...]
    summary: V04SemiSyntheticSummary
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
    output = {}
    ordered_keys = tuple(model.domain.keys)
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


def _posterior_interval(samples, site: str, alpha: float):
    if site not in samples:
        raise KeyError(f"posterior samples missing promotion site {site!r}")
    draws = tuple(float(value) for value in samples[site])
    return (
        sum(draws) / len(draws),
        _quantile(draws, alpha),
        _quantile(draws, 1.0 - alpha),
    )


def summarize_v04_state_activity(
    records: Sequence[V04Replicate],
    *,
    identification,
    extrapolation_integrity: bool,
) -> V04SemiSyntheticSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.4 validation records must be non-empty")
    n = len(rows)
    return V04SemiSyntheticSummary(
        replicates=n,
        positive_structural_pass=identification.positive_structural_pass,
        positive_practical_pass=identification.positive_practical_pass,
        sparse_structural_pass=identification.sparse_structural_pass,
        sparse_practical_refused=identification.sparse_practical_refused,
        unknown_detection_refused=identification.unknown_detection_refused,
        extrapolation_integrity=bool(extrapolation_integrity),
        activity_beta_precip_mean_bias=sum(
            row.activity_beta_precip_mean - 0.55 for row in rows
        ) / n,
        activity_beta_eastness_mean_bias=sum(
            row.activity_beta_eastness_mean - 0.40 for row in rows
        ) / n,
        state_beta_precip_mean_bias=sum(
            row.state_beta_precip_mean - (-0.50) for row in rows
        ) / n,
        state_beta_eastness_mean_bias=sum(
            row.state_beta_eastness_mean - 0.45 for row in rows
        ) / n,
        activity_beta_precip_coverage=sum(
            row.activity_beta_precip_covers_truth for row in rows
        ) / n,
        activity_beta_eastness_coverage=sum(
            row.activity_beta_eastness_covers_truth for row in rows
        ) / n,
        state_beta_precip_coverage=sum(
            row.state_beta_precip_covers_truth for row in rows
        ) / n,
        state_beta_eastness_coverage=sum(
            row.state_beta_eastness_covers_truth for row in rows
        ) / n,
        activity_positive_gain_rate=sum(
            row.activity_gain > 0.0 for row in rows
        ) / n,
        mean_activity_gain=sum(row.activity_gain for row in rows) / n,
        state_positive_gain_rate=sum(
            row.state_gain > 0.0 for row in rows
        ) / n,
        mean_state_gain=sum(row.state_gain for row in rows) / n,
        total_divergences=sum(
            row.full_divergences
            + row.activity_knockout_divergences
            + row.state_knockout_divergences
            for row in rows
        ),
        fit_count=3 * n,
    )


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


def run_v04_state_activity_replicate(
    source_csv_text: str,
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 250,
    num_samples: int = 300,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04Replicate:
    """Run one frozen positive-profile replicate."""

    from esdm.model.backend_numpyro import fit_numpyro

    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    alpha = (1.0 - mass) / 2.0

    fixture = build_v04_state_activity_fixture(
        source_csv_text,
        profile="positive",
    )
    full_train, train_covariates = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout=None,
    )
    activity_train, activity_train_covariates = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout="activity",
    )
    state_train, state_train_covariates = _subset_model(
        fixture,
        fixture.train_spaces,
        knockout="state",
    )
    full_heldout, heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout=None,
    )
    activity_heldout, activity_heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout="activity",
    )
    state_heldout, state_heldout_covariates = _subset_model(
        fixture,
        fixture.heldout_spaces,
        knockout="state",
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

    activity_precip = _posterior_interval(
        full_fit.samples,
        "sp.activity.activity_beta_precip",
        alpha,
    )
    activity_eastness = _posterior_interval(
        full_fit.samples,
        "sp.activity.activity_beta_eastness",
        alpha,
    )
    state_precip = _posterior_interval(
        full_fit.samples,
        "sp.state.beta_foraging_precip",
        alpha,
    )
    state_eastness = _posterior_interval(
        full_fit.samples,
        "sp.state.beta_foraging_eastness",
        alpha,
    )

    full_score = poisson_block_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_covariates,
        heldout_data,
        block_names=V04_STATE_BLOCKS,
    )
    activity_score = poisson_block_log_predictive_density(
        activity_heldout,
        activity_fit.samples,
        activity_heldout_covariates,
        heldout_data,
        block_names=V04_STATE_BLOCKS,
    )
    state_score = poisson_block_log_predictive_density(
        state_heldout,
        state_fit.samples,
        state_heldout_covariates,
        heldout_data,
        block_names=V04_STATE_BLOCKS,
    )

    return V04Replicate(
        replicate=int(replicate),
        activity_beta_precip_mean=activity_precip[0],
        activity_beta_precip_low=activity_precip[1],
        activity_beta_precip_high=activity_precip[2],
        activity_beta_eastness_mean=activity_eastness[0],
        activity_beta_eastness_low=activity_eastness[1],
        activity_beta_eastness_high=activity_eastness[2],
        state_beta_precip_mean=state_precip[0],
        state_beta_precip_low=state_precip[1],
        state_beta_precip_high=state_precip[2],
        state_beta_eastness_mean=state_eastness[0],
        state_beta_eastness_low=state_eastness[1],
        state_beta_eastness_high=state_eastness[2],
        full_heldout_log_score=full_score,
        activity_knockout_heldout_log_score=activity_score,
        state_knockout_heldout_log_score=state_score,
        full_divergences=full_fit.num_divergences,
        activity_knockout_divergences=activity_fit.num_divergences,
        state_knockout_divergences=state_fit.num_divergences,
    )


def run_v04_state_activity_benchmark(
    source_csv_text: str,
    *,
    replicates: int = 16,
    base_seed: int = 20260924,
    seed_stride: int = 43,
    num_warmup: int = 250,
    num_samples: int = 300,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04Result:
    """Run the complete frozen positive-profile benchmark."""

    fixture = build_v04_state_activity_fixture(
        source_csv_text,
        profile="positive",
    )
    identification = evaluate_v04_identification_profiles(source_csv_text)
    rows = []
    for replicate in range(int(replicates)):
        rows.append(
            run_v04_state_activity_replicate(
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
        )
    records = tuple(rows)
    summary = summarize_v04_state_activity(
        records,
        identification=identification,
        extrapolation_integrity=_extrapolation_integrity(fixture),
    )
    return V04Result(
        replicates=records,
        summary=summary,
        train_space_count=len(fixture.train_spaces),
        heldout_space_count=len(fixture.heldout_spaces),
        calibration_space_count=len(fixture.calibration_spaces),
    )
