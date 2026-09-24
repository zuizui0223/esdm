"""Replicated event-gated claim validation for v0.5c."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.claims import bounded_interaction_claim
from esdm.core import InteractionEvidenceTier
from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_run import _quantile, _subset_data
from .v05c_event_validation import (
    V05C_BETA_TARGET,
    V05C_EVENT_SITE,
    V05C_EVENT_SUPPORT_THRESHOLD,
    V05C_WORLDS,
    build_v05c_world,
)


@dataclass(frozen=True, slots=True)
class V05CReplicate:
    world: str
    replicate: int
    truth_beta: float
    true_event_probability: float
    beta_mean: float
    beta_low: float
    beta_high: float
    event_probability_mean: float
    event_probability_low: float
    event_probability_high: float
    training_event_count: int
    claim_tier: str
    divergences: int

    @property
    def beta_positive(self) -> bool:
        return self.beta_low > 0.0

    @property
    def event_supported(self) -> bool:
        return self.event_probability_low > V05C_EVENT_SUPPORT_THRESHOLD

    @property
    def event_covers_truth(self) -> bool:
        return (
            self.event_probability_low
            <= self.true_event_probability
            <= self.event_probability_high
        )

    @property
    def realized_claim(self) -> bool:
        return self.claim_tier == InteractionEvidenceTier.REALIZED.name


@dataclass(frozen=True, slots=True)
class V05CWorldSummary:
    world: str
    replicates: int
    beta_positive_rate: float
    event_support_rate: float
    realized_claim_rate: float
    mean_event_probability: float
    event_probability_bias: float
    event_probability_coverage: float
    mean_training_event_count: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V05CSummary:
    worlds: dict
    total_fits: int
    total_divergences: int


def _subset_fitting_model(fixture, spaces):
    grid = Grid(
        space=tuple(spaces),
        doy=fixture.fitting_model.domain.doy,
        hour=fixture.fitting_model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.fitting_model.species,
        streams=fixture.fitting_model.streams,
    )
    covariates = {
        key: dict(fixture.fitting_covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def _sigmoid(value: float) -> float:
    numeric = float(value)
    if numeric >= 0.0:
        z = math.exp(-numeric)
        return 1.0 / (1.0 + z)
    z = math.exp(numeric)
    return z / (1.0 + z)


def run_v05c_replicate(
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
) -> V05CReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v05c_world(world)
    generated = simulate_observations(
        fixture.generating_model,
        fixture.generating_theta,
        fixture.generating_covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_model, train_covariates = _subset_fitting_model(
        fixture, fixture.train_spaces
    )
    train_data = _subset_data(generated.counts, train_model)

    fit = fit_numpyro(
        train_model,
        train_data,
        train_covariates,
        rng_seed=int(seed) + 1,
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
        progress_bar=bool(progress_bar),
        target_accept_prob=float(target_accept_prob),
    )

    beta_draws = tuple(float(value) for value in fit.samples[V05C_BETA_TARGET])
    event_draws = tuple(
        _sigmoid(float(value))
        for value in fit.samples[V05C_EVENT_SITE]
    )
    alpha = (1.0 - float(credible_mass)) / 2.0
    beta_low = _quantile(beta_draws, alpha)
    event_low = _quantile(event_draws, alpha)
    event_supported = event_low > V05C_EVENT_SUPPORT_THRESHOLD
    distribution_supported = beta_low > 0.0
    claim = bounded_interaction_claim(
        "source->focal",
        distribution_supported=distribution_supported,
        event_supported=event_supported,
        causal_supported=False,
    )

    event_counts = generated.counts["interaction_events"]["focal"]
    train = set(fixture.train_spaces)
    count = sum(
        int(value)
        for key, value in event_counts.items()
        if key[0] in train
    )

    return V05CReplicate(
        world=str(world),
        replicate=int(replicate),
        truth_beta=float(
            fixture.generating_theta["focal"]["beta_partner"]
        ),
        true_event_probability=float(fixture.true_event_probability),
        beta_mean=math.fsum(beta_draws) / len(beta_draws),
        beta_low=beta_low,
        beta_high=_quantile(beta_draws, 1.0 - alpha),
        event_probability_mean=math.fsum(event_draws) / len(event_draws),
        event_probability_low=event_low,
        event_probability_high=_quantile(event_draws, 1.0 - alpha),
        training_event_count=count,
        claim_tier=claim.tier.name,
        divergences=fit.num_divergences,
    )


def summarize_v05c(
    records: Sequence[V05CReplicate],
) -> V05CSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.5c records must be non-empty")
    grouped = {world: [] for world in V05C_WORLDS}
    for row in rows:
        grouped[row.world].append(row)
    if any(not grouped[world] for world in V05C_WORLDS):
        raise ValueError("v0.5c summary requires both worlds")

    summaries = {}
    for world in V05C_WORLDS:
        group = tuple(grouped[world])
        n = len(group)
        true_p = group[0].true_event_probability
        summaries[world] = V05CWorldSummary(
            world=world,
            replicates=n,
            beta_positive_rate=sum(row.beta_positive for row in group) / n,
            event_support_rate=sum(row.event_supported for row in group) / n,
            realized_claim_rate=sum(row.realized_claim for row in group) / n,
            mean_event_probability=math.fsum(
                row.event_probability_mean for row in group
            ) / n,
            event_probability_bias=math.fsum(
                row.event_probability_mean - true_p for row in group
            ) / n,
            event_probability_coverage=sum(
                row.event_covers_truth for row in group
            ) / n,
            mean_training_event_count=math.fsum(
                row.training_event_count for row in group
            ) / n,
            total_divergences=sum(int(row.divergences) for row in group),
        )
    return V05CSummary(
        worlds=summaries,
        total_fits=len(rows),
        total_divergences=sum(int(row.divergences) for row in rows),
    )
