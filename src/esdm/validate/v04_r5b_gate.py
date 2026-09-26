"""Combined qualification + outcome gate for v0.4-R5b."""

from __future__ import annotations

from dataclasses import dataclass

from .v04_r2_gate import V04R2Summary, evaluate_v04_r2_gate
from .v04_r5a_gate import (
    V04R5AQualificationSummary,
    evaluate_v04_r5a_qualification,
)


@dataclass(frozen=True, slots=True)
class V04R5BDecision:
    passed: bool
    qualification_passed: bool
    outcome_passed: bool
    qualification_checks: tuple[object, ...]
    outcome_checks: tuple[object, ...]


def evaluate_v04_r5b_gate(
    qualification: V04R5AQualificationSummary,
    outcome: V04R2Summary,
) -> V04R5BDecision:
    """Require the frozen R5a design and the unchanged R2 full-outcome criteria."""

    qualification_decision = evaluate_v04_r5a_qualification(qualification)
    outcome_decision = evaluate_v04_r2_gate(outcome)
    return V04R5BDecision(
        passed=qualification_decision.passed and outcome_decision.passed,
        qualification_passed=qualification_decision.passed,
        outcome_passed=outcome_decision.passed,
        qualification_checks=qualification_decision.checks,
        outcome_checks=outcome_decision.checks,
    )
