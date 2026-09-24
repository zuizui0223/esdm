"""Replicated evidence-separation benchmark for v0.5e."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.authorization import (
    InteractionEventRecord,
    authorize_interaction_event,
)
from esdm.claims import EdgeClaimEvidence, authorize_biotic_edge_claim
from esdm.core import InteractionEvidenceTier
from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_run import _quantile, _subset_data
from .v05e_fixture import (
    V05E_BETA_SITE,
    V05E_EVENT_SITE,
    V05E_WORLDS,
    build_v05e_fixture,
)


@dataclass(frozen=True, slots=True)
class V05EReplicate:
    world: str
    replicate: int
    beta_truth: float
    beta_mean: float
    beta_interval_low: float
    beta_interval_high: float
    event_truth: float
    event_mean: float
    event_interval_low: float
    event_interval_high: float
    realized_event_count: int
    authorized_tier: str
    divergences: int

    def __post_init__(self) -> None:
        if self.world not in V05E_WORLDS:
            raise ValueError("unknown v0.5e world")

    @property
    def beta_covers_truth(self) -> bool:
        return self.beta_interval_low <= self.beta_truth <= self.beta_interval_high

    @property
    def beta_positive_interval(self) -> bool:
        return self.beta_interval_low > 0.0

    @property
    def beta_nonzero_interval(self) -> bool:
        return (
            self.beta_interval_low > 0.0
            or self.beta_interval_high < 0.0
        )

    @property
    def event_covers_truth(self) -> bool:
        return self.event_interval_low <= self.event_truth <= self.event_interval_high

    @property
    def has_positive_event(self) -> bool:
        return self.realized_event_count > 0


@dataclass(frozen=True, slots=True)
class V05EWorldSummary:
    world: str
    replicates: int
    mean_beta_bias: float
    beta_coverage: float
    beta_positive_interval_rate: float
    beta_nonzero_interval_rate: float
    mean_event_bias: float
    event_coverage: float
    positive_event_rate: float
    predictive_tier_rate: float
    realized_tier_rate: float
    functional_or_higher_rate: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V05ESummary:
    worlds: dict
    total_fits: int
    total_divergences: int


def _training_model(fixture):
    grid = Grid(
        space=fixture.train_spaces,
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


def _event_count(generated) -> int:
    values = generated.counts["events"]["focal"]
    return sum(int(value) for value in values.values())


def _authorized_tier(event_count: int) -> str:
    raw_state = "positive" if int(event_count) > 0 else "negative"
    event = authorize_interaction_event(
        InteractionEventRecord(
            "source",
            "focal",
            "v05e-event",
            raw_state,
            negative_gate_passed=True,
        )
    )
    result = authorize_biotic_edge_claim(
        EdgeClaimEvidence(
            "source",
            "focal",
            InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
            event_observations=(event,),
        ),
        requested_tier=InteractionEvidenceTier.CAUSAL,
    )
    return result.edge.tier.name


def run_v05e_replicate(
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
) -> V05EReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v05e_fixture(world)
    generated = simulate_observations(
        fixture.generating_model,
        fixture.generating_theta,
        fixture.generating_covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    model, covariates = _training_model(fixture)
    data = _subset_data(generated.counts, model)
    fit = fit_numpyro(
        model,
        data,
        covariates,
        rng_seed=int(seed) + 1,
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
        progress_bar=bool(progress_bar),
        target_accept_prob=float(target_accept_prob),
    )

    beta_draws = tuple(float(value) for value in fit.samples[V05E_BETA_SITE])
    event_draws = tuple(float(value) for value in fit.samples[V05E_EVENT_SITE])
    alpha = (1.0 - float(credible_mass)) / 2.0
    event_count = _event_count(generated)
    return V05EReplicate(
        world=str(world),
        replicate=int(replicate),
        beta_truth=float(
            fixture.generating_theta["focal"]["beta_partner"]
        ),
        beta_mean=math.fsum(beta_draws) / len(beta_draws),
        beta_interval_low=_quantile(beta_draws, alpha),
        beta_interval_high=_quantile(beta_draws, 1.0 - alpha),
        event_truth=float(
            fixture.generating_theta_obs["events"]["event_intercept"]
        ),
        event_mean=math.fsum(event_draws) / len(event_draws),
        event_interval_low=_quantile(event_draws, alpha),
        event_interval_high=_quantile(event_draws, 1.0 - alpha),
        realized_event_count=event_count,
        authorized_tier=_authorized_tier(event_count),
        divergences=fit.num_divergences,
    )


def summarize_v05e(records: Sequence[V05EReplicate]) -> V05ESummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.5e records must be non-empty")
    grouped = {world: [] for world in V05E_WORLDS}
    for row in rows:
        grouped[row.world].append(row)
    if any(not grouped[world] for world in V05E_WORLDS):
        raise ValueError("v0.5e summary requires all frozen worlds")

    summaries = {}
    for world in V05E_WORLDS:
        group = tuple(grouped[world])
        n = len(group)
        summaries[world] = V05EWorldSummary(
            world=world,
            replicates=n,
            mean_beta_bias=math.fsum(
                row.beta_mean - row.beta_truth for row in group
            ) / n,
            beta_coverage=sum(row.beta_covers_truth for row in group) / n,
            beta_positive_interval_rate=sum(
                row.beta_positive_interval for row in group
            ) / n,
            beta_nonzero_interval_rate=sum(
                row.beta_nonzero_interval for row in group
            ) / n,
            mean_event_bias=math.fsum(
                row.event_mean - row.event_truth for row in group
            ) / n,
            event_coverage=sum(row.event_covers_truth for row in group) / n,
            positive_event_rate=sum(row.has_positive_event for row in group) / n,
            predictive_tier_rate=sum(
                row.authorized_tier == "PREDICTIVE_DEPENDENCE"
                for row in group
            ) / n,
            realized_tier_rate=sum(
                row.authorized_tier == "REALIZED"
                for row in group
            ) / n,
            functional_or_higher_rate=sum(
                row.authorized_tier in {"FUNCTIONAL", "CAUSAL"}
                for row in group
            ) / n,
            total_divergences=sum(int(row.divergences) for row in group),
        )
    return V05ESummary(
        worlds=summaries,
        total_fits=len(rows),
        total_divergences=sum(int(row.divergences) for row in rows),
    )
