"""Replicated known-truth runner for the v0.5a directed partner gate."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from types import MappingProxyType
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .evidence import poisson_log_predictive_density
from .v04_r2_run import _quantile, _subset_data
from .v05a_directed import (
    V05A_TARGET,
    V05A_WORLDS,
    build_v05a_fixture,
    v05a_beta_truth,
)


@dataclass(frozen=True, slots=True)
class V05AReplicate:
    world: str
    replicate: int
    seed: int
    posterior_mean: float
    interval_low: float
    interval_high: float
    full_heldout_log_score: float
    knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    def __post_init__(self) -> None:
        if self.world not in V05A_WORLDS:
            raise ValueError("unknown v0.5a world")

    @property
    def truth(self) -> float:
        return v05a_beta_truth(self.world)

    @property
    def covers_truth(self) -> bool:
        return self.interval_low <= self.truth <= self.interval_high

    @property
    def nonzero(self) -> bool:
        return self.interval_low > 0.0 or self.interval_high < 0.0

    @property
    def heldout_gain(self) -> float:
        return self.full_heldout_log_score - self.knockout_heldout_log_score


@dataclass(frozen=True, slots=True)
class V05AWorldSummary:
    world: str
    replicates: int
    mean_beta: float
    mean_bias: float
    truth_coverage: float
    nonzero_rate: float
    positive_gain_rate: float
    material_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V05ASummary:
    worlds: Mapping[str, V05AWorldSummary]
    fit_count: int
    total_divergences: int
    extrapolation_integrity: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "worlds", MappingProxyType(dict(self.worlds)))


def _subset_model(fixture, spaces, *, knockout: bool):
    grid = Grid(
        space=tuple(spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    if knockout:
        model = model.knockout("focal", "partner_effect")
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def _extrapolation_integrity(fixture) -> bool:
    key_doy = fixture.model.domain.doy[0]
    key_hour = fixture.model.domain.hour[0]
    train_max = max(
        fixture.covariates[(space, key_doy, key_hour)]["eastness_z_train"]
        for space in fixture.train_spaces
    )
    heldout_min = min(
        fixture.covariates[(space, key_doy, key_hour)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    )
    return heldout_min > train_max


def run_v05a_replicate(
    source_csv_text: str,
    *,
    world: str,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V05AReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v05a_fixture(source_csv_text, world=world)
    full_train, train_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=False
    )
    knockout_train, knockout_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=True
    )
    full_heldout, heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=False
    )
    knockout_heldout, knockout_heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=True
    )

    generated = simulate_observations(
        fixture.model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    full_train_data = _subset_data(generated.counts, full_train)
    knockout_train_data = _subset_data(generated.counts, knockout_train)
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
        full_train_data,
        train_cov,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    knockout_fit = fit_numpyro(
        knockout_train,
        knockout_train_data,
        knockout_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    draws = tuple(float(value) for value in full_fit.samples[V05A_TARGET])
    alpha = (1.0 - float(credible_mass)) / 2.0
    posterior_mean = math.fsum(draws) / len(draws)

    full_score = poisson_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_cov,
        heldout_data,
        stream_name="focal_records",
        species="focal",
    )
    knockout_score = poisson_log_predictive_density(
        knockout_heldout,
        knockout_fit.samples,
        knockout_heldout_cov,
        heldout_data,
        stream_name="focal_records",
        species="focal",
    )

    return V05AReplicate(
        world=str(world),
        replicate=int(replicate),
        seed=int(seed),
        posterior_mean=posterior_mean,
        interval_low=_quantile(draws, alpha),
        interval_high=_quantile(draws, 1.0 - alpha),
        full_heldout_log_score=full_score,
        knockout_heldout_log_score=knockout_score,
        full_divergences=full_fit.num_divergences,
        knockout_divergences=knockout_fit.num_divergences,
    )


def summarize_v05a(records: Sequence[V05AReplicate], *, extrapolation_integrity: bool):
    rows = tuple(records)
    grouped = {world: [] for world in V05A_WORLDS}
    for row in rows:
        grouped[row.world].append(row)
    if any(not grouped[world] for world in V05A_WORLDS):
        raise ValueError("v0.5a summary requires both worlds")

    summaries = {}
    for world in V05A_WORLDS:
        group = tuple(grouped[world])
        truth = v05a_beta_truth(world)
        gains = tuple(row.heldout_gain for row in group)
        summaries[world] = V05AWorldSummary(
            world=world,
            replicates=len(group),
            mean_beta=math.fsum(row.posterior_mean for row in group) / len(group),
            mean_bias=math.fsum(
                row.posterior_mean - truth for row in group
            ) / len(group),
            truth_coverage=sum(row.covers_truth for row in group) / len(group),
            nonzero_rate=sum(row.nonzero for row in group) / len(group),
            positive_gain_rate=sum(gain > 0.0 for gain in gains) / len(group),
            material_gain_rate=sum(gain > 0.005 for gain in gains) / len(group),
            mean_heldout_gain=math.fsum(gains) / len(group),
            total_divergences=sum(
                row.full_divergences + row.knockout_divergences
                for row in group
            ),
        )
    return V05ASummary(
        worlds=summaries,
        fit_count=2 * len(rows),
        total_divergences=sum(
            row.full_divergences + row.knockout_divergences
            for row in rows
        ),
        extrapolation_integrity=bool(extrapolation_integrity),
    )
