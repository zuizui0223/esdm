"""Frozen null-refusal evaluator for v0.5b hidden-common-driver stress."""

from __future__ import annotations

from dataclasses import dataclass

from .v05b_run import V05BSummary


@dataclass(frozen=True, slots=True)
class V05BGateConfig:
    replicates: int = 16
    max_abs_mean_beta: float = 0.10
    min_zero_coverage: float = 0.75
    max_nonzero_interval_rate: float = 0.25
    max_mean_heldout_gain: float = 0.005
    max_material_gain_rate: float = 0.25
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V05BGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05BDecision:
    passed: bool
    checks: tuple[V05BGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V05BGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05b_gate(
    summary: V05BSummary,
    *,
    config: V05BGateConfig = V05BGateConfig(),
) -> V05BDecision:
    mean_divergences = (
        float("inf")
        if summary.fit_count <= 0
        else summary.total_divergences / summary.fit_count
    )
    checks = (
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
            "mean_beta",
            abs(summary.mean_beta) <= config.max_abs_mean_beta,
            summary.mean_beta,
            f"abs(mean beta) <= {config.max_abs_mean_beta}",
        ),
        _check(
            "zero_coverage",
            summary.zero_coverage >= config.min_zero_coverage,
            summary.zero_coverage,
            f">= {config.min_zero_coverage}",
        ),
        _check(
            "nonzero_interval_rate",
            summary.nonzero_interval_rate <= config.max_nonzero_interval_rate,
            summary.nonzero_interval_rate,
            f"<= {config.max_nonzero_interval_rate}",
        ),
        _check(
            "mean_heldout_gain",
            summary.mean_heldout_gain <= config.max_mean_heldout_gain,
            summary.mean_heldout_gain,
            f"<= {config.max_mean_heldout_gain}",
        ),
        _check(
            "material_gain_rate",
            summary.heldout_material_gain_rate <= config.max_material_gain_rate,
            summary.heldout_material_gain_rate,
            f"<= {config.max_material_gain_rate}",
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V05BDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
