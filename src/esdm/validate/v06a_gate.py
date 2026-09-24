"""Mechanical gate for v0.6a accessibility recovery/transfer."""

from __future__ import annotations

from dataclasses import dataclass

from .v06a_fixture import V06A_RECOVERY_TRUTH
from .v06a_qualification import V06AQualification
from .v06a_run import V06ASummary


@dataclass(frozen=True, slots=True)
class V06AGateConfig:
    replicates: int = 16
    max_abs_mean_bias: float = 0.15
    min_coverage: float = 0.75
    min_positive_gain_rate: float = 0.75
    min_mean_gain: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V06AGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V06ADecision:
    passed: bool
    checks: tuple[V06AGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V06AGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v06a_gate(
    qualification: V06AQualification,
    summary: V06ASummary,
    *,
    config: V06AGateConfig = V06AGateConfig(),
) -> V06ADecision:
    checks = [
        _check(
            "positive_structural_pass",
            qualification.positive_structural_pass,
            qualification.positive_structural_pass,
            "is True",
        ),
        _check(
            "positive_practical_pass",
            qualification.positive_practical_pass,
            qualification.positive_practical_pass,
            "is True",
        ),
        _check(
            "joint_only_refusal_pass",
            qualification.joint_only_refusal_pass,
            qualification.joint_only_refusal_pass,
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
    ]
    for target in V06A_RECOVERY_TRUTH:
        checks.append(
            _check(
                f"bias:{target}",
                abs(summary.mean_biases[target]) <= config.max_abs_mean_bias,
                summary.mean_biases[target],
                f"abs(mean bias) <= {config.max_abs_mean_bias}",
            )
        )
        checks.append(
            _check(
                f"coverage:{target}",
                summary.coverages[target] >= config.min_coverage,
                summary.coverages[target],
                f">= {config.min_coverage}",
            )
        )
    checks.extend([
        _check(
            "positive_gain_rate",
            summary.positive_gain_rate >= config.min_positive_gain_rate,
            summary.positive_gain_rate,
            f">= {config.min_positive_gain_rate}",
        ),
        _check(
            "mean_gain",
            summary.mean_gain >= config.min_mean_gain,
            summary.mean_gain,
            f">= {config.min_mean_gain}",
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
    ])
    return V06ADecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
