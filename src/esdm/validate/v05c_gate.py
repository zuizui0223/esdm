"""Mechanical claim-firewall gate for fresh v0.5c event validation."""

from __future__ import annotations

from dataclasses import dataclass

from .v05c_run import V05CSummary


@dataclass(frozen=True, slots=True)
class V05CGateConfig:
    replicates_per_world: int = 16
    true_min_beta_positive_rate: float = 0.75
    true_min_event_support_rate: float = 0.75
    true_min_realized_claim_rate: float = 0.75
    true_max_abs_event_probability_bias: float = 0.08
    true_min_event_probability_coverage: float = 0.75
    null_max_event_support_rate: float = 0.25
    null_max_realized_claim_rate: float = 0.25
    null_max_mean_event_probability: float = 0.05
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V05CGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05CDecision:
    passed: bool
    checks: tuple[V05CGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V05CGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05c_gate(
    summary: V05CSummary,
    *,
    config: V05CGateConfig = V05CGateConfig(),
) -> V05CDecision:
    true = summary.worlds["interaction_event"]
    null = summary.worlds["hidden_driver_null"]
    mean_divergences = (
        float("inf")
        if summary.total_fits <= 0
        else summary.total_divergences / summary.total_fits
    )
    checks = (
        _check(
            "true_replicates",
            true.replicates == config.replicates_per_world,
            true.replicates,
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
            summary.total_fits == 2 * config.replicates_per_world,
            summary.total_fits,
            f"== {2 * config.replicates_per_world}",
        ),
        _check(
            "true_beta_positive_rate",
            true.beta_positive_rate >= config.true_min_beta_positive_rate,
            true.beta_positive_rate,
            f">= {config.true_min_beta_positive_rate}",
        ),
        _check(
            "true_event_support_rate",
            true.event_support_rate >= config.true_min_event_support_rate,
            true.event_support_rate,
            f">= {config.true_min_event_support_rate}",
        ),
        _check(
            "true_realized_claim_rate",
            true.realized_claim_rate >= config.true_min_realized_claim_rate,
            true.realized_claim_rate,
            f">= {config.true_min_realized_claim_rate}",
        ),
        _check(
            "true_event_probability_bias",
            abs(true.event_probability_bias)
            <= config.true_max_abs_event_probability_bias,
            true.event_probability_bias,
            f"abs(bias) <= {config.true_max_abs_event_probability_bias}",
        ),
        _check(
            "true_event_probability_coverage",
            true.event_probability_coverage
            >= config.true_min_event_probability_coverage,
            true.event_probability_coverage,
            f">= {config.true_min_event_probability_coverage}",
        ),
        _check(
            "null_event_support_rate",
            null.event_support_rate <= config.null_max_event_support_rate,
            null.event_support_rate,
            f"<= {config.null_max_event_support_rate}",
        ),
        _check(
            "null_realized_claim_rate",
            null.realized_claim_rate <= config.null_max_realized_claim_rate,
            null.realized_claim_rate,
            f"<= {config.null_max_realized_claim_rate}",
        ),
        _check(
            "null_mean_event_probability",
            null.mean_event_probability
            <= config.null_max_mean_event_probability,
            null.mean_event_probability,
            f"<= {config.null_max_mean_event_probability}",
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V05CDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
