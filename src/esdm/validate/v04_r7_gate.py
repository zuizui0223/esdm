"""Mechanical gate for v0.4-R7 budget-matched calibration comparison."""

from __future__ import annotations

from dataclasses import dataclass

from .v04_r7_run import V04R7Summary


@dataclass(frozen=True, slots=True)
class V04R7GateConfig:
    replicates: int = 16
    expected_label_budget: float = 432.0
    budget_tolerance: float = 1e-8
    min_heldout_positive_gain_rate: float = 0.75
    min_mean_heldout_gain: float = 0.005
    min_state_error_positive_gain_rate: float = 0.75
    min_mean_state_error_gain: float = 0.0
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V04R7GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04R7Decision:
    passed: bool
    checks: tuple[V04R7GateCheck, ...]


def _check(name, passed, observed, criterion):
    return V04R7GateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v04_r7_gate(
    summary: V04R7Summary,
    *,
    config: V04R7GateConfig = V04R7GateConfig(),
) -> V04R7Decision:
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
            "shared_base_data",
            summary.all_shared_base_data_equal,
            summary.all_shared_base_data_equal,
            "is True",
        ),
        _check(
            "direct_expected_label_budget",
            abs(summary.direct_expected_labels - config.expected_label_budget)
            <= config.budget_tolerance,
            summary.direct_expected_labels,
            f"== {config.expected_label_budget}",
        ),
        _check(
            "passive_expected_label_budget",
            abs(summary.passive_expected_labels - config.expected_label_budget)
            <= config.budget_tolerance,
            summary.passive_expected_labels,
            f"== {config.expected_label_budget}",
        ),
        _check(
            "heldout_positive_gain_rate",
            summary.heldout_positive_gain_rate
            >= config.min_heldout_positive_gain_rate,
            summary.heldout_positive_gain_rate,
            f">= {config.min_heldout_positive_gain_rate}",
        ),
        _check(
            "mean_heldout_gain",
            summary.mean_heldout_gain >= config.min_mean_heldout_gain,
            summary.mean_heldout_gain,
            f">= {config.min_mean_heldout_gain}",
        ),
        _check(
            "state_error_positive_gain_rate",
            summary.state_error_positive_gain_rate
            >= config.min_state_error_positive_gain_rate,
            summary.state_error_positive_gain_rate,
            f">= {config.min_state_error_positive_gain_rate}",
        ),
        _check(
            "mean_state_error_gain",
            summary.mean_state_error_gain > config.min_mean_state_error_gain,
            summary.mean_state_error_gain,
            f"> {config.min_mean_state_error_gain}",
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V04R7Decision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
