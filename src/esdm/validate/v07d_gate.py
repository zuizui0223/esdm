"""Mechanical frozen gate for v0.7d equal-dimension benchmark."""

from __future__ import annotations

from dataclasses import dataclass

from .v07d_qualification import V07DQualification
from .v07d_run import V07DSummary


@dataclass(frozen=True, slots=True)
class V07DGateConfig:
    replicates: int = 16
    min_dynamic_better_rate: float = 0.875
    min_mean_dynamic_gain: float = 0.50
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07DGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07DDecision:
    passed: bool
    checks: tuple[V07DGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07DGateCheck(
        str(name),
        bool(passed),
        observed,
        str(criterion),
    )


def evaluate_v07d_gate(
    qualification: V07DQualification,
    summary: V07DSummary,
    *,
    config: V07DGateConfig = V07DGateConfig(),
) -> V07DDecision:
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
            "dynamic_better_rate",
            summary.dynamic_better_rate >= config.min_dynamic_better_rate,
            summary.dynamic_better_rate,
            f">= {config.min_dynamic_better_rate}",
        ),
        _check(
            "mean_dynamic_gain",
            summary.mean_dynamic_gain >= config.min_mean_dynamic_gain,
            summary.mean_dynamic_gain,
            f">= {config.min_mean_dynamic_gain}",
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
    return V07DDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
