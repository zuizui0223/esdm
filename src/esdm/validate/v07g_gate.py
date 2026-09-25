"""Mechanical MCMC validation gate for v0.7g calibration placement."""

from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07g_run import V07GSummary


@dataclass(frozen=True, slots=True)
class V07GGateConfig:
    replicates: int = 16
    min_optimized_lower_worst_sd_rate: float = 0.75
    max_mean_worst_sd_ratio: float = 0.85
    max_abs_mean_bias: float = 0.15
    min_coverage: float = 0.75
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07GGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07GDecision:
    passed: bool
    checks: tuple[V07GGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07GGateCheck(
        str(name), bool(passed), observed, str(criterion)
    )


def evaluate_v07g_gate(
    summary: V07GSummary,
    *,
    config: V07GGateConfig = V07GGateConfig(),
) -> V07GDecision:
    checks = [
        _check(
            "replicates",
            summary.replicates == config.replicates,
            summary.replicates,
            f"== {config.replicates}",
        ),
        _check(
            "fit_count",
            summary.fit_count == 2 * config.replicates,
            summary.fit_count,
            f"== {2 * config.replicates}",
        ),
        _check(
            "optimized_lower_worst_sd_rate",
            summary.optimized_lower_worst_sd_rate
            >= config.min_optimized_lower_worst_sd_rate,
            summary.optimized_lower_worst_sd_rate,
            f">= {config.min_optimized_lower_worst_sd_rate}",
        ),
        _check(
            "mean_worst_sd_ratio",
            summary.mean_worst_sd_ratio
            <= config.max_mean_worst_sd_ratio,
            summary.mean_worst_sd_ratio,
            f"<= {config.max_mean_worst_sd_ratio}",
        ),
    ]

    for target in V07B_TRUTH:
        checks.append(
            _check(
                f"optimized_bias:{target}",
                abs(summary.optimized_mean_biases[target])
                <= config.max_abs_mean_bias,
                summary.optimized_mean_biases[target],
                f"abs(mean bias) <= {config.max_abs_mean_bias}",
            )
        )
        checks.append(
            _check(
                f"optimized_coverage:{target}",
                summary.optimized_coverages[target] >= config.min_coverage,
                summary.optimized_coverages[target],
                f">= {config.min_coverage}",
            )
        )

    checks.append(
        _check(
            "mean_divergences_per_fit",
            (
                summary.total_divergences / summary.fit_count
                if summary.fit_count
                else float("inf")
            )
            <= config.max_mean_divergences_per_fit,
            (
                summary.total_divergences / summary.fit_count
                if summary.fit_count
                else float("inf")
            ),
            f"<= {config.max_mean_divergences_per_fit}",
        )
    )

    return V07GDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
