"""Mechanical gate for v0.5f interaction-transfer replication."""
from __future__ import annotations

from dataclasses import dataclass

from .v05a_gate import V05ADecision, V05AGateConfig, evaluate_v05a_gate
from .v05a_qualification import V05AQualification
from .v05f_run import V05FSummary


@dataclass(frozen=True, slots=True)
class V05FGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05FDecision:
    passed: bool
    inherited_v05a_decision: V05ADecision
    checks: tuple[V05FGateCheck, ...]


def evaluate_v05f_gate(
    qualification: V05AQualification,
    summary: V05FSummary,
) -> V05FDecision:
    """Apply unchanged v0.5a thresholds plus absolute-score serialization."""

    inherited = evaluate_v05a_gate(
        qualification,
        summary.inherited_v05a,
        config=V05AGateConfig(),
    )

    checks = [
        V05FGateCheck(
            name=row.name,
            passed=row.passed,
            observed=row.observed,
            criterion=row.criterion,
        )
        for row in inherited.checks
    ]
    checks.append(
        V05FGateCheck(
            name="absolute_score_serialization",
            passed=summary.max_abs_gain_identity_error <= 1e-12,
            observed=summary.max_abs_gain_identity_error,
            criterion="max abs((full - knockout) - gain) <= 1e-12",
        )
    )
    return V05FDecision(
        passed=bool(inherited.passed and checks[-1].passed),
        inherited_v05a_decision=inherited,
        checks=tuple(checks),
    )
