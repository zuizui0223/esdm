"""Mechanical gate for fresh v0.5a directed-effect known-truth worlds."""

from __future__ import annotations

from dataclasses import dataclass

from .v05a_qualification import V05AQualification
from .v05a_run import V05ASummary


@dataclass(frozen=True, slots=True)
class V05AGateConfig:
    replicates_per_world: int = 16
    positive_max_abs_bias: float = 0.15
    positive_min_coverage: float = 0.75
    positive_min_interval_rate: float = 0.75
    positive_min_gain_rate: float = 0.75
    positive_min_mean_gain: float = 0.005
    null_max_abs_mean: float = 0.10
    null_min_coverage: float = 0.75
    null_max_nonzero_rate: float = 0.25
    null_max_mean_gain: float = 0.005
    null_max_material_gain_rate: float = 0.25
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V05AGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05ADecision:
    passed: bool
    checks: tuple[V05AGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V05AGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05a_gate(
    qualification: V05AQualification,
    summary: V05ASummary,
    *,
    config: V05AGateConfig = V05AGateConfig(),
) -> V05ADecision:
    positive = summary.worlds["interaction"]
    null = summary.worlds["measured_shared_null"]
    mean_divergences = (
        float("inf")
        if summary.total_fits <= 0
        else summary.total_divergences / summary.total_fits
    )
    checks = (
        _check(
            "interaction_structural_pass",
            qualification.interaction_structural_pass,
            qualification.interaction_structural_pass,
            "is True",
        ),
        _check(
            "interaction_practical_pass",
            qualification.interaction_practical_pass,
            qualification.interaction_practical_pass,
            "is True",
        ),
        _check(
            "null_structural_pass",
            qualification.null_structural_pass,
            qualification.null_structural_pass,
            "is True",
        ),
        _check(
            "null_practical_pass",
            qualification.null_practical_pass,
            qualification.null_practical_pass,
            "is True",
        ),
        _check(
            "positive_replicates",
            positive.replicates == config.replicates_per_world,
            positive.replicates,
            f"== {config.replicates_per_world}",
        ),
        _check(
            "null_replicates",
            null.replicates == config.replicates_per_world,
            null.replicates,
            f"== {config.replicates_per_world}",
        ),
        _check(
            "total_fits",
            summary.total_fits == 4 * config.replicates_per_world,
            summary.total_fits,
            f"== {4 * config.replicates_per_world}",
        ),
        _check(
            "positive_bias",
            abs(positive.mean_bias) <= config.positive_max_abs_bias,
            positive.mean_bias,
            f"abs(mean bias) <= {config.positive_max_abs_bias}",
        ),
        _check(
            "positive_coverage",
            positive.coverage >= config.positive_min_coverage,
            positive.coverage,
            f">= {config.positive_min_coverage}",
        ),
        _check(
            "positive_interval_rate",
            positive.positive_interval_rate >= config.positive_min_interval_rate,
            positive.positive_interval_rate,
            f">= {config.positive_min_interval_rate}",
        ),
        _check(
            "positive_gain_rate",
            positive.heldout_positive_gain_rate >= config.positive_min_gain_rate,
            positive.heldout_positive_gain_rate,
            f">= {config.positive_min_gain_rate}",
        ),
        _check(
            "positive_mean_gain",
            positive.mean_heldout_gain >= config.positive_min_mean_gain,
            positive.mean_heldout_gain,
            f">= {config.positive_min_mean_gain}",
        ),
        _check(
            "null_mean_beta",
            abs(null.mean_bias) <= config.null_max_abs_mean,
            null.mean_bias,
            f"abs(mean beta) <= {config.null_max_abs_mean}",
        ),
        _check(
            "null_coverage",
            null.coverage >= config.null_min_coverage,
            null.coverage,
            f">= {config.null_min_coverage}",
        ),
        _check(
            "null_nonzero_rate",
            null.nonzero_interval_rate <= config.null_max_nonzero_rate,
            null.nonzero_interval_rate,
            f"<= {config.null_max_nonzero_rate}",
        ),
        _check(
            "null_mean_gain",
            null.mean_heldout_gain <= config.null_max_mean_gain,
            null.mean_heldout_gain,
            f"<= {config.null_max_mean_gain}",
        ),
        _check(
            "null_material_gain_rate",
            null.heldout_material_gain_rate <= config.null_max_material_gain_rate,
            null.heldout_material_gain_rate,
            f"<= {config.null_max_material_gain_rate}",
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V05ADecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
