"""Mechanical decision rule for the frozen TR1 trait-transfer programme."""
from __future__ import annotations

from dataclasses import dataclass

from .tr1_trait_transfer import TR1WorldSummary


@dataclass(frozen=True, slots=True)
class TR1GateConfig:
    replicates_per_world: int = 32
    positive_mean_gain_minimum: float = 0.03
    positive_gain_rate_minimum: float = 0.75
    positive_abs_trait_bias_maximum: float = 0.15
    null_material_gain_count_maximum: int = 8
    null_mean_gain_maximum: float = 0.005
    null_abs_mean_trait_coefficient_maximum: float = 0.15


@dataclass(frozen=True, slots=True)
class TR1GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class TR1Decision:
    passed: bool
    checks: tuple[TR1GateCheck, ...]


def _check(name, passed, observed, criterion):
    return TR1GateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_tr1_gate(
    positive: TR1WorldSummary,
    null: TR1WorldSummary,
    *,
    config: TR1GateConfig = TR1GateConfig(),
) -> TR1Decision:
    if positive.world != "positive":
        raise ValueError("positive summary must have world='positive'")
    if null.world != "null":
        raise ValueError("null summary must have world='null'")

    checks = (
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
            "positive_mean_gain",
            positive.mean_gain >= config.positive_mean_gain_minimum,
            positive.mean_gain,
            f">= {config.positive_mean_gain_minimum}",
        ),
        _check(
            "positive_gain_rate",
            positive.positive_gain_rate >= config.positive_gain_rate_minimum,
            positive.positive_gain_rate,
            f">= {config.positive_gain_rate_minimum}",
        ),
        _check(
            "positive_trait_bias",
            abs(positive.mean_trait_coefficient_bias)
            <= config.positive_abs_trait_bias_maximum,
            positive.mean_trait_coefficient_bias,
            f"abs(mean bias) <= {config.positive_abs_trait_bias_maximum}",
        ),
        _check(
            "null_material_gain_count",
            null.material_gain_count <= config.null_material_gain_count_maximum,
            null.material_gain_count,
            f"<= {config.null_material_gain_count_maximum}",
        ),
        _check(
            "null_mean_gain",
            null.mean_gain <= config.null_mean_gain_maximum,
            null.mean_gain,
            f"<= {config.null_mean_gain_maximum}",
        ),
        _check(
            "null_mean_trait_coefficient",
            abs(null.mean_fitted_trait_coefficient)
            <= config.null_abs_mean_trait_coefficient_maximum,
            null.mean_fitted_trait_coefficient,
            f"abs(mean fitted beta_trait) <= {config.null_abs_mean_trait_coefficient_maximum}",
        ),
    )
    return TR1Decision(
        passed=all(row.passed for row in checks),
        checks=checks,
    )
