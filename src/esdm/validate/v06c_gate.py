"""Mechanical gate for v0.6c budget-matched accessibility evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .v06a_fixture import V06A_RECOVERY_TRUTH
from .v06c_fixture import V06C_ACCESS_TARGETS
from .v06c_qualification import V06CQualification
from .v06c_run import V06CSummary


@dataclass(frozen=True, slots=True)
class V06CGateConfig:
    replicates: int = 16
    max_relative_expected_budget_error: float = 1e-12
    max_qualification_access_sd_ratio: float = 0.50
    max_direct_abs_mean_bias: float = 0.15
    min_direct_coverage: float = 0.75
    min_direct_lower_sd_rate: float = 0.875
    max_mean_posterior_sd_ratio: float = 0.75
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V06CGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V06CDecision:
    passed: bool
    checks: tuple[V06CGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V06CGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v06c_gate(
    qualification: V06CQualification,
    summary: V06CSummary,
    *,
    config: V06CGateConfig = V06CGateConfig(),
) -> V06CDecision:
    checks = [
        _check(
            "expected_aux_budget_match",
            qualification.relative_budget_error
            <= config.max_relative_expected_budget_error,
            qualification.relative_budget_error,
            f"<= {config.max_relative_expected_budget_error}",
        ),
        _check(
            "direct_all_structural",
            qualification.direct_all_structural,
            qualification.direct_all_structural,
            "is True",
        ),
        _check(
            "direct_all_practical",
            qualification.direct_all_practical,
            qualification.direct_all_practical,
            "is True",
        ),
        _check(
            "matched_all_structural",
            qualification.matched_all_structural,
            qualification.matched_all_structural,
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
    for target in V06C_ACCESS_TARGETS:
        checks.append(
            _check(
                f"qualification_sd_ratio:{target}",
                qualification.access_sd_proxy_ratios[target]
                <= config.max_qualification_access_sd_ratio,
                qualification.access_sd_proxy_ratios[target],
                f"<= {config.max_qualification_access_sd_ratio}",
            )
        )
        checks.append(
            _check(
                f"direct_lower_sd_rate:{target}",
                summary.direct_lower_sd_rates[target]
                >= config.min_direct_lower_sd_rate,
                summary.direct_lower_sd_rates[target],
                f">= {config.min_direct_lower_sd_rate}",
            )
        )
        checks.append(
            _check(
                f"mean_posterior_sd_ratio:{target}",
                summary.mean_sd_ratios[target]
                <= config.max_mean_posterior_sd_ratio,
                summary.mean_sd_ratios[target],
                f"<= {config.max_mean_posterior_sd_ratio}",
            )
        )
    for target in V06A_RECOVERY_TRUTH:
        checks.append(
            _check(
                f"direct_bias:{target}",
                abs(summary.direct_mean_biases[target])
                <= config.max_direct_abs_mean_bias,
                summary.direct_mean_biases[target],
                f"abs(mean bias) <= {config.max_direct_abs_mean_bias}",
            )
        )
        checks.append(
            _check(
                f"direct_coverage:{target}",
                summary.direct_coverages[target]
                >= config.min_direct_coverage,
                summary.direct_coverages[target],
                f">= {config.min_direct_coverage}",
            )
        )
    mean_div = (
        float("inf")
        if summary.fit_count <= 0
        else summary.total_divergences / summary.fit_count
    )
    checks.append(
        _check(
            "mean_divergences_per_fit",
            mean_div <= config.max_mean_divergences_per_fit,
            mean_div,
            f"<= {config.max_mean_divergences_per_fit}",
        )
    )
    return V06CDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
