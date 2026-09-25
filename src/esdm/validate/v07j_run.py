"""Paired population-shift validation for v0.7j."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _quantile
from .v07g_fixture import V07G_DYNAMIC_TARGETS
from .v07g_run import _heldout_score, _posterior_sd, _training_data
from .v07j_fixture import V07J_WORLD_ORDER, build_v07j_fixture, truth_sites


@dataclass(frozen=True, slots=True)
class V07JReplicate:
    world: str
    replicate: int
    selected_posterior_sds: dict
    baseline_posterior_sds: dict
    selected_posterior_means: dict
    selected_posterior_lows: dict
    selected_posterior_highs: dict
    selected_heldout_log_score: float
    baseline_heldout_log_score: float
    selected_divergences: int
    baseline_divergences: int

    def __post_init__(self) -> None:
        truth = truth_sites(self.world)
        expected = set(truth)
        for name in (
            "selected_posterior_sds",
            "baseline_posterior_sds",
            "selected_posterior_means",
            "selected_posterior_lows",
            "selected_posterior_highs",
        ):
            values = {
                str(key): float(value)
                for key, value in getattr(self, name).items()
            }
            if set(values) != expected:
                raise ValueError(
                    f"{name} targets must match frozen v0.7j truth for {self.world}"
                )
            object.__setattr__(self, name, MappingProxyType(values))

    @property
    def selected_worst_dynamic_sd(self) -> float:
        return max(
            self.selected_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def baseline_worst_dynamic_sd(self) -> float:
        return max(
            self.baseline_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def worst_sd_ratio(self) -> float:
        return self.selected_worst_dynamic_sd / self.baseline_worst_dynamic_sd

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.selected_heldout_log_score)
            - float(self.baseline_heldout_log_score)
        )

    def selected_covers_truth(self, target: str) -> bool:
        truth = truth_sites(self.world)[target]
        return (
            self.selected_posterior_lows[target]
            <= truth
            <= self.selected_posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V07JWorldSummary:
    world: str
    replicates: int
    fit_count: int
    selected_lower_worst_sd_rate: float
    mean_worst_sd_ratio: float
    minimum_worst_sd_ratio: float
    maximum_worst_sd_ratio: float
    selected_mean_biases: dict
    selected_coverages: dict
    positive_heldout_gain_rate: float
    mean_heldout_gain: float
    minimum_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07JSummary:
    world_summaries: dict
    total_replicates: int
    total_fit_count: int
    total_divergences: int
    pooled_mean_worst_sd_ratio: float
    pooled_selected_lower_worst_sd_rate: float


def run_v07j_replicate(
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
) -> V07JReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07j_fixture(world)
    generated = simulate_observations(
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )

    selected_data = _training_data(
        generated.counts,
        fixture,
        fixture.selected_keys,
    )
    baseline_data = _training_data(
        generated.counts,
        fixture,
        fixture.baseline_keys,
    )
    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    selected_fit = fit_numpyro(
        fixture.selected_model,
        selected_data,
        fixture.covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    baseline_fit = fit_numpyro(
        fixture.baseline_model,
        baseline_data,
        fixture.covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    selected_sds = {}
    baseline_sds = {}
    means = {}
    lows = {}
    highs = {}
    for target in truth_sites(world):
        selected_draws = tuple(
            float(value) for value in selected_fit.samples[target]
        )
        baseline_draws = tuple(
            float(value) for value in baseline_fit.samples[target]
        )
        selected_sds[target] = _posterior_sd(selected_draws)
        baseline_sds[target] = _posterior_sd(baseline_draws)
        means[target] = math.fsum(selected_draws) / len(selected_draws)
        lows[target] = _quantile(selected_draws, alpha)
        highs[target] = _quantile(selected_draws, 1.0 - alpha)

    selected_score = _heldout_score(
        fixture.scoring_model,
        selected_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )
    baseline_score = _heldout_score(
        fixture.scoring_model,
        baseline_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )

    return V07JReplicate(
        world=world,
        replicate=int(replicate),
        selected_posterior_sds=selected_sds,
        baseline_posterior_sds=baseline_sds,
        selected_posterior_means=means,
        selected_posterior_lows=lows,
        selected_posterior_highs=highs,
        selected_heldout_log_score=float(selected_score),
        baseline_heldout_log_score=float(baseline_score),
        selected_divergences=int(selected_fit.num_divergences),
        baseline_divergences=int(baseline_fit.num_divergences),
    )


def summarize_v07j_world(records: Sequence[V07JReplicate]) -> V07JWorldSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7j world records must be non-empty")
    worlds = {row.world for row in rows}
    if len(worlds) != 1:
        raise ValueError("v0.7j world summary cannot mix target worlds")
    world = next(iter(worlds))
    truth = truth_sites(world)
    n = len(rows)
    ratios = tuple(row.worst_sd_ratio for row in rows)
    gains = tuple(row.heldout_gain for row in rows)

    biases = {}
    coverages = {}
    for target, target_truth in truth.items():
        biases[target] = math.fsum(
            row.selected_posterior_means[target] - float(target_truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.selected_covers_truth(target) for row in rows
        ) / n

    return V07JWorldSummary(
        world=world,
        replicates=n,
        fit_count=2 * n,
        selected_lower_worst_sd_rate=sum(
            row.selected_worst_dynamic_sd < row.baseline_worst_dynamic_sd
            for row in rows
        ) / n,
        mean_worst_sd_ratio=math.fsum(ratios) / n,
        minimum_worst_sd_ratio=min(ratios),
        maximum_worst_sd_ratio=max(ratios),
        selected_mean_biases=biases,
        selected_coverages=coverages,
        positive_heldout_gain_rate=sum(gain > 0.0 for gain in gains) / n,
        mean_heldout_gain=math.fsum(gains) / n,
        minimum_heldout_gain=min(gains),
        total_divergences=sum(
            int(row.selected_divergences) + int(row.baseline_divergences)
            for row in rows
        ),
    )


def summarize_v07j(records: Sequence[V07JReplicate]) -> V07JSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7j records must be non-empty")
    summaries = {}
    for world in V07J_WORLD_ORDER:
        local = tuple(row for row in rows if row.world == world)
        summaries[world] = summarize_v07j_world(local)

    ratios = tuple(row.worst_sd_ratio for row in rows)
    return V07JSummary(
        world_summaries=summaries,
        total_replicates=len(rows),
        total_fit_count=2 * len(rows),
        total_divergences=sum(
            int(row.selected_divergences) + int(row.baseline_divergences)
            for row in rows
        ),
        pooled_mean_worst_sd_ratio=math.fsum(ratios) / len(ratios),
        pooled_selected_lower_worst_sd_rate=sum(
            row.selected_worst_dynamic_sd < row.baseline_worst_dynamic_sd
            for row in rows
        ) / len(rows),
    )
