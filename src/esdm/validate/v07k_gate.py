"""Mechanical local re-pilot rescue gate for v0.7k."""

from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07k_fixture import V07K_WORLDS
from .v07k_run import V07KSummary


@dataclass(frozen=True, slots=True)
class V07KGateConfig:
    replicates_per_world: int = 16
    min_adaptive_lower_worst_sd_rate: float = 0.75
    max_mean_worst_sd_ratio: float = 0.95
    max_abs_mean_bias: float = 0.20
    min_coverage: float = 0.75
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07KGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07KDecision:
    passed: bool
    checks: tuple[V07KGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07KGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07k_gate(
    summary: V07KSummary,
    *,
    config: V07KGateConfig = V07KGateConfig(),
) -> V07KDecision:
    total_reps = config.replicates_per_world * len(V07K_WORLDS)
    checks = [
        _check(
            "replicates",
            summary.replicates == total_reps,
            summary.replicates,
            f"== {total_reps}",
        ),
        _check(
            "fit_count",
            summary.fit_count == 3 * total_reps,
            summary.fit_count,
            f"== {3 * total_reps}",
        ),
    ]
    for world in V07K_WORLDS:
        row = summary.worlds[world]
        checks.append(_check(
            f"{world}:replicates",
            row.replicates == config.replicates_per_world,
            row.replicates,
            f"== {config.replicates_per_world}",
        ))
        checks.append(_check(
            f"{world}:adaptive_lower_worst_sd_rate",
            row.adaptive_lower_worst_sd_rate
            >= config.min_adaptive_lower_worst_sd_rate,
            row.adaptive_lower_worst_sd_rate,
            f">= {config.min_adaptive_lower_worst_sd_rate}",
        ))
        checks.append(_check(
            f"{world}:mean_worst_sd_ratio",
            row.mean_worst_sd_ratio <= config.max_mean_worst_sd_ratio,
            row.mean_worst_sd_ratio,
            f"<= {config.max_mean_worst_sd_ratio}",
        ))
        for target in V07B_TRUTH:
            checks.append(_check(
                f"{world}:adaptive_bias:{target}",
                abs(row.adaptive_mean_biases[target])
                <= config.max_abs_mean_bias,
                row.adaptive_mean_biases[target],
                f"abs(mean bias) <= {config.max_abs_mean_bias}",
            ))
            checks.append(_check(
                f"{world}:adaptive_coverage:{target}",
                row.adaptive_coverages[target] >= config.min_coverage,
                row.adaptive_coverages[target],
                f">= {config.min_coverage}",
            ))

    checks.append(_check(
        "mean_divergences_per_fit",
        (
            summary.total_divergences / summary.fit_count
            if summary.fit_count else float("inf")
        ) <= config.max_mean_divergences_per_fit,
        (
            summary.total_divergences / summary.fit_count
            if summary.fit_count else float("inf")
        ),
        f"<= {config.max_mean_divergences_per_fit}",
    ))
    return V07KDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
