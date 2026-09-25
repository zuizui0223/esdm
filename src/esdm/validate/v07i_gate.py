"""Mechanical disjoint burned-pilot adaptive-design gate for v0.7i."""

from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07i_run import V07ISummary


@dataclass(frozen=True, slots=True)
class V07IGateConfig:
    replicates: int = 16
    min_selected_lower_worst_sd_rate: float = 0.75
    max_mean_worst_sd_ratio: float = 0.90
    max_abs_mean_bias: float = 0.15
    min_coverage: float = 0.75
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07IGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07IDecision:
    passed: bool
    checks: tuple[V07IGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07IGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07i_gate(
    summary: V07ISummary,
    *,
    config: V07IGateConfig = V07IGateConfig(),
) -> V07IDecision:
    checks = [
        _check(
            "replicates",
            summary.replicates == config.replicates,
            summary.replicates,
            f"== {config.replicates}",
        ),
        _check(
            "fit_count",
            summary.fit_count == 3 * config.replicates,
            summary.fit_count,
            f"== {3 * config.replicates}",
        ),
        _check(
            "selected_lower_worst_sd_rate",
            summary.selected_lower_worst_sd_rate
            >= config.min_selected_lower_worst_sd_rate,
            summary.selected_lower_worst_sd_rate,
            f">= {config.min_selected_lower_worst_sd_rate}",
        ),
        _check(
            "mean_worst_sd_ratio",
            summary.mean_worst_sd_ratio <= config.max_mean_worst_sd_ratio,
            summary.mean_worst_sd_ratio,
            f"<= {config.max_mean_worst_sd_ratio}",
        ),
    ]
    for target in V07B_TRUTH:
        checks.append(
            _check(
                f"selected_bias:{target}",
                abs(summary.selected_mean_biases[target])
                <= config.max_abs_mean_bias,
                summary.selected_mean_biases[target],
                f"abs(mean bias) <= {config.max_abs_mean_bias}",
            )
        )
        checks.append(
            _check(
                f"selected_coverage:{target}",
                summary.selected_coverages[target] >= config.min_coverage,
                summary.selected_coverages[target],
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
            ) <= config.max_mean_divergences_per_fit,
            (
                summary.total_divergences / summary.fit_count
                if summary.fit_count
                else float("inf")
            ),
            f"<= {config.max_mean_divergences_per_fit}",
        )
    )
    return V07IDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
