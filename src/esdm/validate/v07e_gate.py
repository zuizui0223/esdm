"""Mechanical reciprocal static-world specificity gate for v0.7e."""

from __future__ import annotations

from dataclasses import dataclass

from .v07e_qualification import V07EQualification
from .v07e_run import V07ESummary


@dataclass(frozen=True, slots=True)
class V07EGateConfig:
    replicates: int = 16
    min_static_better_rate: float = 0.875
    min_mean_static_gain: float = 0.50
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07EGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07EDecision:
    passed: bool
    checks: tuple[V07EGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07EGateCheck(
        str(name),
        bool(passed),
        observed,
        str(criterion),
    )


def evaluate_v07e_gate(
    qualification: V07EQualification,
    summary: V07ESummary,
    *,
    config: V07EGateConfig = V07EGateConfig(),
) -> V07EDecision:
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
            "static_better_rate",
            summary.static_better_rate >= config.min_static_better_rate,
            summary.static_better_rate,
            f">= {config.min_static_better_rate}",
        ),
        _check(
            "mean_static_gain",
            summary.mean_static_gain >= config.min_mean_static_gain,
            summary.mean_static_gain,
            f">= {config.min_mean_static_gain}",
        ),
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
        ),
    ]
    return V07EDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
