"""Matched full-resolution versus collapsed-resolution benchmark for v0.4-R6."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping, Sequence
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_run import _state_block_log_predictive_density, _subset_data
from .v04_r5a_design import build_v04_r5a_fixture


R6_WORLDS = ("structured", "resolution_null")

R6_ACTIVITY_SLOPES = (
    "activity_beta_precip",
    "activity_beta_eastness",
    "activity_beta_season",
    "activity_beta_hour",
)

R6_STATE_SLOPES = (
    "beta_foraging_precip",
    "beta_foraging_eastness",
    "beta_foraging_season",
    "beta_foraging_hour",
)


@dataclass(frozen=True, slots=True)
class V04R6Replicate:
    world: str
    replicate: int
    seed: int
    full_heldout_log_score: float
    collapsed_heldout_log_score: float
    full_divergences: int
    collapsed_divergences: int

    def __post_init__(self) -> None:
        if self.world not in R6_WORLDS:
            raise ValueError("unknown R6 world")
        if int(self.replicate) < 0:
            raise ValueError("replicate must be non-negative")

    @property
    def resolution_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.collapsed_heldout_log_score)
        )


@dataclass(frozen=True, slots=True)
class V04R6WorldSummary:
    world: str
    replicates: int
    positive_gain_rate: float
    material_gain_rate: float
    mean_gain: float
    min_gain: float
    max_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V04R6Summary:
    worlds: Mapping[str, V04R6WorldSummary]
    total_fits: int
    total_divergences: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "worlds", MappingProxyType(dict(self.worlds)))


def _subset_candidate_model(fixture, spaces, *, collapsed: bool):
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
    if collapsed:
        model = model.knockout("sp", "activity")
        model = model.knockout("sp", "state")
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def r6_generating_theta(fixture, world: str):
    normalized = str(world)
    if normalized not in R6_WORLDS:
        raise ValueError("unknown R6 world")
    theta = {
        species: dict(values)
        for species, values in fixture.generating_theta.items()
    }
    if normalized == "resolution_null":
        for parameter in (*R6_ACTIVITY_SLOPES, *R6_STATE_SLOPES):
            theta["sp"][parameter] = 0.0
    return theta


def run_v04_r6_replicate(
    source_csv_text: str,
    *,
    world: str,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V04R6Replicate:
    """Generate once, fit matched candidates, and score the same east-heldout data."""

    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v04_r5a_fixture(source_csv_text)
    theta = r6_generating_theta(fixture, world)

    full_train, train_covariates = _subset_candidate_model(
        fixture, fixture.train_spaces, collapsed=False
    )
    collapsed_train, collapsed_covariates = _subset_candidate_model(
        fixture, fixture.train_spaces, collapsed=True
    )
    full_heldout, heldout_covariates = _subset_candidate_model(
        fixture, fixture.heldout_spaces, collapsed=False
    )
    collapsed_heldout, collapsed_heldout_covariates = _subset_candidate_model(
        fixture, fixture.heldout_spaces, collapsed=True
    )

    generated = simulate_observations(
        fixture.model,
        theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_data = _subset_data(generated.counts, full_train)
    collapsed_train_data = _subset_data(generated.counts, collapsed_train)
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
    collapsed_fit = fit_numpyro(
        collapsed_train,
        collapsed_train_data,
        collapsed_covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    full_score = _state_block_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_covariates,
        heldout_data,
    )
    collapsed_score = _state_block_log_predictive_density(
        collapsed_heldout,
        collapsed_fit.samples,
        collapsed_heldout_covariates,
        heldout_data,
    )
    return V04R6Replicate(
        world=str(world),
        replicate=int(replicate),
        seed=int(seed),
        full_heldout_log_score=full_score,
        collapsed_heldout_log_score=collapsed_score,
        full_divergences=full_fit.num_divergences,
        collapsed_divergences=collapsed_fit.num_divergences,
    )


def summarize_v04_r6(
    records: Sequence[V04R6Replicate],
    *,
    material_gain_threshold: float = 0.005,
) -> V04R6Summary:
    rows = tuple(records)
    if not rows:
        raise ValueError("R6 records must be non-empty")
    threshold = float(material_gain_threshold)
    grouped = {world: [] for world in R6_WORLDS}
    for row in rows:
        grouped[row.world].append(row)
    if any(not grouped[world] for world in R6_WORLDS):
        raise ValueError("R6 summary requires both frozen worlds")

    summaries = {}
    for world in R6_WORLDS:
        group = tuple(grouped[world])
        gains = tuple(row.resolution_gain for row in group)
        n = len(group)
        summaries[world] = V04R6WorldSummary(
            world=world,
            replicates=n,
            positive_gain_rate=sum(gain > 0.0 for gain in gains) / n,
            material_gain_rate=sum(gain > threshold for gain in gains) / n,
            mean_gain=math.fsum(gains) / n,
            min_gain=min(gains),
            max_gain=max(gains),
            total_divergences=sum(
                int(row.full_divergences) + int(row.collapsed_divergences)
                for row in group
            ),
        )
    return V04R6Summary(
        worlds=summaries,
        total_fits=2 * len(rows),
        total_divergences=sum(
            int(row.full_divergences) + int(row.collapsed_divergences)
            for row in rows
        ),
    )
