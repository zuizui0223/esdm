"""Mechanical fresh-MCMC population-shift gate for v0.7j."""

from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07j_confirm import V07J_WORLDS
from .v07j_run import V07JSummary


@dataclass(frozen=True, slots=True)
class V07JGateConfig:
    replicates_per_world: int = 16
    min_correct_direction_rate: float = 0.75
    max_positive_mean_ratio: float = 0.95
    min_reversal_mean_ratio: float = 1.10
    max_abs_mean_bias: float = 0.20
    min_coverage: float = 0.75
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
    return V07JGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07j_gate(
    summary: V07JSummary,
    *,
    config: V07JGateConfig = V07JGateConfig(),
) -> V07JDecision:
    total_reps = config.replicates_per_world * len(V07J_WORLDS)
    checks = [
        _check("replicates", summary.replicates == total_reps,
               summary.replicates, f"== {total_reps}"),
        _check("fit_count", summary.fit_count == 2 * total_reps,
               summary.fit_count, f"== {2 * total_reps}"),
    ]
    for world in V07J_WORLDS:
        row = summary.worlds[world]
        checks.append(_check(
            f"{world}:replicates",
            row.replicates == config.replicates_per_world,
            row.replicates,
            f"== {config.replicates_per_world}",
        ))
        checks.append(_check(
            f"{world}:correct_direction_rate",
            row.correct_direction_rate >= config.min_correct_direction_rate,
            row.correct_direction_rate,
            f">= {config.min_correct_direction_rate}",
        ))
        if world == "transfer_positive":
            checks.append(_check(
                "transfer_positive:mean_ratio",
                row.mean_selected_to_baseline_ratio
                <= config.max_positive_mean_ratio,
                row.mean_selected_to_baseline_ratio,
                f"<= {config.max_positive_mean_ratio}",
            ))
        else:
            checks.append(_check(
                "reversal:mean_ratio",
                row.mean_selected_to_baseline_ratio
                >= config.min_reversal_mean_ratio,
                row.mean_selected_to_baseline_ratio,
                f">= {config.min_reversal_mean_ratio}",
            ))
        for target in V07B_TRUTH:
            checks.append(_check(
                f"{world}:winner_bias:{target}",
                abs(row.winner_mean_biases[target])
                <= config.max_abs_mean_bias,
                row.winner_mean_biases[target],
                f"abs(mean bias) <= {config.max_abs_mean_bias}",
            ))
            checks.append(_check(
                f"{world}:winner_coverage:{target}",
                row.winner_coverages[target] >= config.min_coverage,
                row.winner_coverages[target],
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
    return V07JDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
