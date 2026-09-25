"""Paired MCMC validation of v0.7g calibration placement."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import (
    V07G_DYNAMIC_TARGETS,
    build_v07g_validation_fixture,
)


@dataclass(frozen=True, slots=True)
class V07GReplicate:
    replicate: int
    optimized_posterior_sds: dict
    baseline_posterior_sds: dict
    optimized_posterior_means: dict
    optimized_posterior_lows: dict
    optimized_posterior_highs: dict
    optimized_heldout_log_score: float
    baseline_heldout_log_score: float
    optimized_divergences: int
    baseline_divergences: int

    def __post_init__(self) -> None:
        expected = set(V07B_TRUTH)
        for name in (
            "optimized_posterior_sds",
            "baseline_posterior_sds",
            "optimized_posterior_means",
            "optimized_posterior_lows",
            "optimized_posterior_highs",
        ):
            raw = getattr(self, name)
            values = {str(key): float(value) for key, value in raw.items()}
            if set(values) != expected:
                raise ValueError(
                    f"{name} targets must match frozen v0.7g targets"
                )
            object.__setattr__(self, name, MappingProxyType(values))

    @property
    def optimized_worst_dynamic_sd(self) -> float:
        return max(
            self.optimized_posterior_sds[target]
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
        return (
            self.optimized_worst_dynamic_sd
            / self.baseline_worst_dynamic_sd
        )

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.optimized_heldout_log_score)
            - float(self.baseline_heldout_log_score)
        )

    def optimized_covers_truth(self, target: str) -> bool:
        truth = float(V07B_TRUTH[target])
        return (
            self.optimized_posterior_lows[target]
            <= truth
            <= self.optimized_posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V07GSummary:
    replicates: int
    fit_count: int
    optimized_lower_worst_sd_rate: float
    mean_worst_sd_ratio: float
    minimum_worst_sd_ratio: float
    maximum_worst_sd_ratio: float
    optimized_mean_biases: dict
    optimized_coverages: dict
    positive_heldout_gain_rate: float
    mean_heldout_gain: float
    minimum_heldout_gain: float
    total_divergences: int


def _training_data(generated_counts, fixture, keys):
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.source.joint_train_keys
            }
        },
        "occupancy_calibration": {
            "sp": {
                key: int(
                    generated_counts["occupancy_calibration"]["sp"][key]
                )
                for key in keys
            }
        },
    }


def _posterior_sd(values) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("posterior SD requires at least one draw")
    mean = math.fsum(rows) / len(rows)
    return math.sqrt(
        math.fsum((value - mean) ** 2 for value in rows) / len(rows)
    )


def _heldout_score(model, samples, covariates, generated_counts, heldout_keys):
    from esdm.model.backend_numpyro import posterior_observation_rates

    rates_by_block = posterior_observation_rates(model, samples, covariates)
    block_name = "joint.sp"
    if block_name not in rates_by_block:
        raise KeyError(f"posterior rates missing {block_name!r}")
    draws = tuple(rates_by_block[block_name])
    keys = tuple(model.domain.keys)
    index_by_key = {key: index for index, key in enumerate(keys)}

    scores = []
    for key in heldout_keys:
        index = index_by_key[key]
        count = int(generated_counts["joint"]["sp"][key])
        scores.append(
            _logmeanexp(
                _poisson_log_mass(count, draw[index])
                for draw in draws
            )
        )
    return math.fsum(scores) / len(scores)


def run_v07g_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07GReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07g_validation_fixture()
    generated = simulate_observations(
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )

    optimized_data = _training_data(
        generated.counts,
        fixture,
        fixture.optimized_keys,
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
    optimized_fit = fit_numpyro(
        fixture.optimized_model,
        optimized_data,
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
    optimized_sds = {}
    baseline_sds = {}
    means = {}
    lows = {}
    highs = {}
    for target in V07B_TRUTH:
        optimized_draws = tuple(
            float(value) for value in optimized_fit.samples[target]
        )
        baseline_draws = tuple(
            float(value) for value in baseline_fit.samples[target]
        )
        optimized_sds[target] = _posterior_sd(optimized_draws)
        baseline_sds[target] = _posterior_sd(baseline_draws)
        means[target] = math.fsum(optimized_draws) / len(optimized_draws)
        lows[target] = _quantile(optimized_draws, alpha)
        highs[target] = _quantile(optimized_draws, 1.0 - alpha)

    optimized_score = _heldout_score(
        fixture.scoring_model,
        optimized_fit.samples,
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

    return V07GReplicate(
        replicate=int(replicate),
        optimized_posterior_sds=optimized_sds,
        baseline_posterior_sds=baseline_sds,
        optimized_posterior_means=means,
        optimized_posterior_lows=lows,
        optimized_posterior_highs=highs,
        optimized_heldout_log_score=optimized_score,
        baseline_heldout_log_score=baseline_score,
        optimized_divergences=optimized_fit.num_divergences,
        baseline_divergences=baseline_fit.num_divergences,
    )


def summarize_v07g(records: Sequence[V07GReplicate]) -> V07GSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7g records must be non-empty")
    n = len(rows)
    ratios = tuple(row.worst_sd_ratio for row in rows)
    gains = tuple(row.heldout_gain for row in rows)

    mean_biases = {}
    coverages = {}
    for target, truth in V07B_TRUTH.items():
        mean_biases[target] = math.fsum(
            row.optimized_posterior_means[target] - float(truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.optimized_covers_truth(target)
            for row in rows
        ) / n

    return V07GSummary(
        replicates=n,
        fit_count=2 * n,
        optimized_lower_worst_sd_rate=sum(
            row.optimized_worst_dynamic_sd
            < row.baseline_worst_dynamic_sd
            for row in rows
        ) / n,
        mean_worst_sd_ratio=math.fsum(ratios) / n,
        minimum_worst_sd_ratio=min(ratios),
        maximum_worst_sd_ratio=max(ratios),
        optimized_mean_biases=mean_biases,
        optimized_coverages=coverages,
        positive_heldout_gain_rate=sum(gain > 0.0 for gain in gains) / n,
        mean_heldout_gain=math.fsum(gains) / n,
        minimum_heldout_gain=min(gains),
        total_divergences=sum(
            int(row.optimized_divergences) + int(row.baseline_divergences)
            for row in rows
        ),
    )
