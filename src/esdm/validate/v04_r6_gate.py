"""Mechanical gate for the v0.4-R6 matched resolution benchmark."""

from __future__ import annotations

from dataclasses import dataclass

from .v04_r6_matched import V04R6Summary


@dataclass(frozen=True, slots=True)
class V04R6GateConfig:
    replicates_per_world: int = 16
    structured_min_positive_rate: float = 0.75
    structured_min_mean_gain: float = 0.005
    null_max_mean_gain: float = 0.005
    null_max_material_gain_rate: float = 0.25
    material_gain_threshold: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V04R6GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04R6Decision:
    passed: bool
    checks: tuple[V04R6GateCheck, ...]


def _check(name, passed, observed, criterion):
    return V04R6GateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v04_r6_gate(
    summary: V04R6Summary,
    *,
    config: V04R6GateConfig = V04R6GateConfig(),
) -> V04R6Decision:
    structured = summary.worlds["structured"]
    null = summary.worlds["resolution_null"]

    mean_divergences = (
        float("inf")
        if summary.total_fits <= 0
        else summary.total_divergences / summary.total_fits
    )

    checks = (
        _check(
            "structured_replicates",
            structured.replicates == config.replicates_per_world,
            structured.replicates,
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
            "structured_positive_gain_rate",
            structured.positive_gain_rate >= config.structured_min_positive_rate,
            structured.positive_gain_rate,
            f">= {config.structured_min_positive_rate}",
        ),
        _check(
            "structured_mean_gain",
            structured.mean_gain >= config.structured_min_mean_gain,
            structured.mean_gain,
            f">= {config.structured_min_mean_gain}",
        ),
        _check(
            "null_mean_gain",
            null.mean_gain <= config.null_max_mean_gain,
            null.mean_gain,
            f"<= {config.null_max_mean_gain}",
        ),
        _check(
            "null_material_gain_rate",
            null.material_gain_rate <= config.null_max_material_gain_rate,
            null.material_gain_rate,
            (
                f"proportion(gain > {config.material_gain_threshold}) "
                f"<= {config.null_max_material_gain_rate}"
            ),
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V04R6Decision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
