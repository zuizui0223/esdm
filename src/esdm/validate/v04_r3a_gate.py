"""Pure mechanical qualification conjunction for v0.4-R3a."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class V04R3AQualificationSummary:
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    annotated_context_count: int
    annotated_space_count: int
    annotated_time_count: int
    calibrated_context_count: int
    r2_prefix_preserved: bool


@dataclass(frozen=True, slots=True)
class V04R3ACheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04R3ADecision:
    passed: bool
    checks: tuple[V04R3ACheck, ...]


def _check(name, passed, observed, criterion) -> V04R3ACheck:
    return V04R3ACheck(
        name=str(name),
        passed=bool(passed),
        observed=observed,
        criterion=str(criterion),
    )


def evaluate_v04_r3a_qualification(
    summary: V04R3AQualificationSummary,
) -> V04R3ADecision:
    """Apply the frozen ten-term R3a qualification conjunction."""

    checks = (
        _check(
            "positive_structural_pass",
            summary.positive_structural_pass,
            summary.positive_structural_pass,
            "is True",
        ),
        _check(
            "positive_practical_pass",
            summary.positive_practical_pass,
            summary.positive_practical_pass,
            "is True",
        ),
        _check(
            "sparse_structural_pass",
            summary.sparse_structural_pass,
            summary.sparse_structural_pass,
            "is True",
        ),
        _check(
            "sparse_practical_refused",
            summary.sparse_practical_refused,
            summary.sparse_practical_refused,
            "is True",
        ),
        _check(
            "unknown_detection_refused",
            summary.unknown_detection_refused,
            summary.unknown_detection_refused,
            "is True",
        ),
        _check(
            "annotated_context_count",
            summary.annotated_context_count == 432,
            summary.annotated_context_count,
            "== 432",
        ),
        _check(
            "annotated_space_count",
            summary.annotated_space_count == 36,
            summary.annotated_space_count,
            "== 36",
        ),
        _check(
            "annotated_time_count",
            summary.annotated_time_count == 12,
            summary.annotated_time_count,
            "== 12",
        ),
        _check(
            "calibrated_context_count",
            summary.calibrated_context_count == 432,
            summary.calibrated_context_count,
            "== 432",
        ),
        _check(
            "r2_prefix_preserved",
            summary.r2_prefix_preserved,
            summary.r2_prefix_preserved,
            "is True",
        ),
    )
    return V04R3ADecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
