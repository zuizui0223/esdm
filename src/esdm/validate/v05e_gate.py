"""Mechanical gate for v0.5e evidence separation."""

from __future__ import annotations

from dataclasses import dataclass

from .v05e_run import V05ESummary


@dataclass(frozen=True, slots=True)
class V05EGateConfig:
    replicates_per_world: int = 16
    hidden_max_positive_event_rate: float = 0.25
    hidden_min_predictive_tier_rate: float = 0.75
    realized_min_positive_event_rate: float = 0.875
    realized_min_realized_tier_rate: float = 0.875
    directed_max_abs_beta_bias: float = 0.15
    directed_min_beta_coverage: float = 0.75
    directed_min_positive_interval_rate: float = 0.75
    realized_only_max_abs_beta_bias: float = 0.15
    realized_only_min_beta_coverage: float = 0.75
    realized_only_max_nonzero_interval_rate: float = 0.25
    realized_event_max_abs_bias: float = 0.30
    realized_event_min_coverage: float = 0.75
    max_functional_or_higher_rate: float = 0.0
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V05EGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05EDecision:
    passed: bool
    checks: tuple[V05EGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V05EGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05e_gate(
    summary: V05ESummary,
    *,
    config: V05EGateConfig = V05EGateConfig(),
) -> V05EDecision:
    hidden = summary.worlds["hidden_event_silent"]
    realized = summary.worlds["realized_only"]
    directed = summary.worlds["directed_realized"]
    mean_divergences = (
        float("inf")
        if summary.total_fits <= 0
        else summary.total_divergences / summary.total_fits
    )
    checks = (
        *(
            _check(
                f"{world}_replicates",
                summary.worlds[world].replicates == config.replicates_per_world,
                summary.worlds[world].replicates,
                f"== {config.replicates_per_world}",
            )
            for world in summary.worlds
        ),
        _check(
            "total_fits",
            summary.total_fits == 3 * config.replicates_per_world,
            summary.total_fits,
            f"== {3 * config.replicates_per_world}",
        ),
        _check(
            "hidden_positive_event_rate",
            hidden.positive_event_rate <= config.hidden_max_positive_event_rate,
            hidden.positive_event_rate,
            f"<= {config.hidden_max_positive_event_rate}",
        ),
        _check(
            "hidden_predictive_tier_rate",
            hidden.predictive_tier_rate >= config.hidden_min_predictive_tier_rate,
            hidden.predictive_tier_rate,
            f">= {config.hidden_min_predictive_tier_rate}",
        ),
        _check(
            "realized_positive_event_rate",
            realized.positive_event_rate >= config.realized_min_positive_event_rate,
            realized.positive_event_rate,
            f">= {config.realized_min_positive_event_rate}",
        ),
        _check(
            "realized_tier_rate",
            realized.realized_tier_rate >= config.realized_min_realized_tier_rate,
            realized.realized_tier_rate,
            f">= {config.realized_min_realized_tier_rate}",
        ),
        _check(
            "directed_positive_event_rate",
            directed.positive_event_rate >= config.realized_min_positive_event_rate,
            directed.positive_event_rate,
            f">= {config.realized_min_positive_event_rate}",
        ),
        _check(
            "directed_realized_tier_rate",
            directed.realized_tier_rate >= config.realized_min_realized_tier_rate,
            directed.realized_tier_rate,
            f">= {config.realized_min_realized_tier_rate}",
        ),
        _check(
            "realized_only_beta_bias",
            abs(realized.mean_beta_bias) <= config.realized_only_max_abs_beta_bias,
            realized.mean_beta_bias,
            f"abs(mean bias) <= {config.realized_only_max_abs_beta_bias}",
        ),
        _check(
            "realized_only_beta_coverage",
            realized.beta_coverage >= config.realized_only_min_beta_coverage,
            realized.beta_coverage,
            f">= {config.realized_only_min_beta_coverage}",
        ),
        _check(
            "realized_only_nonzero_beta_rate",
            realized.beta_nonzero_interval_rate
            <= config.realized_only_max_nonzero_interval_rate,
            realized.beta_nonzero_interval_rate,
            f"<= {config.realized_only_max_nonzero_interval_rate}",
        ),
        _check(
            "directed_beta_bias",
            abs(directed.mean_beta_bias) <= config.directed_max_abs_beta_bias,
            directed.mean_beta_bias,
            f"abs(mean bias) <= {config.directed_max_abs_beta_bias}",
        ),
        _check(
            "directed_beta_coverage",
            directed.beta_coverage >= config.directed_min_beta_coverage,
            directed.beta_coverage,
            f">= {config.directed_min_beta_coverage}",
        ),
        _check(
            "directed_positive_beta_rate",
            directed.beta_positive_interval_rate
            >= config.directed_min_positive_interval_rate,
            directed.beta_positive_interval_rate,
            f">= {config.directed_min_positive_interval_rate}",
        ),
        _check(
            "realized_event_bias",
            abs(realized.mean_event_bias) <= config.realized_event_max_abs_bias,
            realized.mean_event_bias,
            f"abs(mean bias) <= {config.realized_event_max_abs_bias}",
        ),
        _check(
            "realized_event_coverage",
            realized.event_coverage >= config.realized_event_min_coverage,
            realized.event_coverage,
            f">= {config.realized_event_min_coverage}",
        ),
        _check(
            "directed_event_bias",
            abs(directed.mean_event_bias) <= config.realized_event_max_abs_bias,
            directed.mean_event_bias,
            f"abs(mean bias) <= {config.realized_event_max_abs_bias}",
        ),
        _check(
            "directed_event_coverage",
            directed.event_coverage >= config.realized_event_min_coverage,
            directed.event_coverage,
            f">= {config.realized_event_min_coverage}",
        ),
        _check(
            "no_functional_or_higher_hidden",
            hidden.functional_or_higher_rate <= config.max_functional_or_higher_rate,
            hidden.functional_or_higher_rate,
            "== 0",
        ),
        _check(
            "no_functional_or_higher_realized",
            realized.functional_or_higher_rate <= config.max_functional_or_higher_rate,
            realized.functional_or_higher_rate,
            "== 0",
        ),
        _check(
            "no_functional_or_higher_directed",
            directed.functional_or_higher_rate <= config.max_functional_or_higher_rate,
            directed.functional_or_higher_rate,
            "== 0",
        ),
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        ),
    )
    return V05EDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
