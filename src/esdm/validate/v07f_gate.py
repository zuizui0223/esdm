"""Mechanical out-of-family resolution-robustness gate for v0.7f."""

from __future__ import annotations

from dataclasses import dataclass

from .v07f_fixture import V07F_WORLDS
from .v07f_qualification import V07FQualification
from .v07f_run import V07FSummary


@dataclass(frozen=True, slots=True)
class V07FGateConfig:
    replicates_per_world: int = 16
    min_correct_better_rate: float = 0.75
    min_mean_correct_gain: float = 0.25
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07FGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07FDecision:
    passed: bool
    checks: tuple[V07FGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07FGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07f_gate(
    qualification: V07FQualification,
    summary: V07FSummary,
    *,
    config: V07FGateConfig = V07FGateConfig(),
) -> V07FDecision:
    checks = [
        _check(
            "dynamic_structural_pass",
            qualification.dynamic_structural_pass,
            qualification.dynamic_structural_pass,
            "is True",
        ),
        _check(
            "dynamic_practical_pass",
            qualification.dynamic_practical_pass,
            qualification.dynamic_practical_pass,
            "is True",
        ),
        _check(
            "static_structural_pass",
            qualification.static_structural_pass,
            qualification.static_structural_pass,
            "is True",
        ),
        _check(
            "static_practical_pass",
            qualification.static_practical_pass,
            qualification.static_practical_pass,
            "is True",
        ),
    ]

    expected_total = config.replicates_per_world * len(V07F_WORLDS)
    checks.extend([
        _check(
            "replicates",
            summary.replicates == expected_total,
            summary.replicates,
            f"== {expected_total}",
        ),
        _check(
            "fit_count",
            summary.fit_count == 2 * expected_total,
            summary.fit_count,
            f"== {2 * expected_total}",
        ),
    ])

    for world in V07F_WORLDS:
        row = summary.worlds[world]
        checks.extend([
            _check(
                f"{world}:replicates",
                row.replicates == config.replicates_per_world,
                row.replicates,
                f"== {config.replicates_per_world}",
            ),
            _check(
                f"{world}:correct_better_rate",
                row.correct_better_rate >= config.min_correct_better_rate,
                row.correct_better_rate,
                f">= {config.min_correct_better_rate}",
            ),
            _check(
                f"{world}:mean_correct_gain",
                row.mean_correct_gain >= config.min_mean_correct_gain,
                row.mean_correct_gain,
                f">= {config.min_mean_correct_gain}",
            ),
        ])

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

    return V07FDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
