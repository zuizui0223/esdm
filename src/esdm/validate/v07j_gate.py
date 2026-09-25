"""Mechanical population-shift robustness gate for v0.7j."""
from __future__ import annotations

from dataclasses import dataclass

from .v07j_fixture import V07J_WORLD_ORDER, truth_sites
from .v07j_run import V07JSummary


@dataclass(frozen=True, slots=True)
class V07JGateConfig:
    replicates_per_world: int = 12
    min_selected_lower_worst_sd_rate: float = 0.75
    max_mean_worst_sd_ratio: float = 0.95
    max_abs_mean_bias: float = 0.20
    min_coverage: float = 2.0 / 3.0
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07JGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07JDecision:
    passed: bool
    checks: tuple[V07JGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07JGateCheck(
        str(name), bool(passed), observed, str(criterion)
    )


def evaluate_v07j_gate(
    summary: V07JSummary,
    *,
    config: V07JGateConfig = V07JGateConfig(),
) -> V07JDecision:
    checks = []
    expected_total_replicates = (
        config.replicates_per_world * len(V07J_WORLD_ORDER)
    )
    checks.extend(
        [
            _check(
                "total_replicates",
                summary.total_replicates == expected_total_replicates,
                summary.total_replicates,
                f"== {expected_total_replicates}",
            ),
            _check(
                "total_fit_count",
                summary.total_fit_count == 2 * expected_total_replicates,
                summary.total_fit_count,
                f"== {2 * expected_total_replicates}",
            ),
        ]
    )

    for world in V07J_WORLD_ORDER:
        row = summary.world_summaries[world]
        checks.extend(
            [
                _check(
                    f"{world}:replicates",
                    row.replicates == config.replicates_per_world,
                    row.replicates,
                    f"== {config.replicates_per_world}",
                ),
                _check(
                    f"{world}:selected_lower_worst_sd_rate",
                    row.selected_lower_worst_sd_rate
                    >= config.min_selected_lower_worst_sd_rate,
                    row.selected_lower_worst_sd_rate,
                    f">= {config.min_selected_lower_worst_sd_rate}",
                ),
                _check(
                    f"{world}:mean_worst_sd_ratio",
                    row.mean_worst_sd_ratio <= config.max_mean_worst_sd_ratio,
                    row.mean_worst_sd_ratio,
                    f"<= {config.max_mean_worst_sd_ratio}",
                ),
            ]
        )
        for target in truth_sites(world):
            checks.append(
                _check(
                    f"{world}:bias:{target}",
                    abs(row.selected_mean_biases[target])
                    <= config.max_abs_mean_bias,
                    row.selected_mean_biases[target],
                    f"abs(mean bias) <= {config.max_abs_mean_bias}",
                )
            )
            checks.append(
                _check(
                    f"{world}:coverage:{target}",
                    row.selected_coverages[target] >= config.min_coverage,
                    row.selected_coverages[target],
                    f">= {config.min_coverage}",
                )
            )

    checks.append(
        _check(
            "mean_divergences_per_fit",
            (
                summary.total_divergences / summary.total_fit_count
                if summary.total_fit_count
                else float("inf")
            )
            <= config.max_mean_divergences_per_fit,
            (
                summary.total_divergences / summary.total_fit_count
                if summary.total_fit_count
                else float("inf")
            ),
            f"<= {config.max_mean_divergences_per_fit}",
        )
    )

    return V07JDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
