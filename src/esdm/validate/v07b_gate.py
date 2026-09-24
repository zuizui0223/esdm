"""Mechanical promotion gate for frozen v0.7b recovery/transfer."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .v07b_fixture import V07B_RECOVERY_TRUTH
from .v07b_qualification import V07BQualification
from .v07b_run import V07BSummary


@dataclass(frozen=True, slots=True)
class V07BGateConfig:
    replicates: int = 16
    max_abs_mean_bias: float = 0.25
    min_coverage: float = 0.75
    min_positive_gain_rate: float = 0.75
    min_mean_gain: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07BGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07BDecision:
    passed: bool
    checks: tuple[V07BGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07BGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07b_gate(
    qualification: V07BQualification,
    summary: V07BSummary,
    *,
    config: V07BGateConfig = V07BGateConfig(),
) -> V07BDecision:
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
    for target in V07B_RECOVERY_TRUTH:
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
    checks.extend(
        [
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
                "absolute_score_serialization",
                math.isclose(
                    summary.mean_full_heldout_log_score
                    - summary.mean_knockout_heldout_log_score,
                    summary.mean_gain,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                ),
                {
                    "full": summary.mean_full_heldout_log_score,
                    "knockout": summary.mean_knockout_heldout_log_score,
                    "gain": summary.mean_gain,
                },
                "mean_full_score - mean_knockout_score == mean_gain",
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
    )
    return V07BDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
