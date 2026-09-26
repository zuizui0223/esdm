"""Mechanical selective-adaptation policy gate for frozen v0.7l."""
from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07l_fixture import V07L_WORLDS
from .v07l_run import V07LSummary


@dataclass(frozen=True, slots=True)
class V07LGateConfig:
    replicates_per_world: int = 16
    min_trigger_rate_below_threshold: float = 0.75
    max_trigger_rate_above_threshold: float = 0.25
    min_actual_headroom_rate_below_threshold: float = 0.75
    max_actual_headroom_rate_above_threshold: float = 0.25
    min_trigger_sensitivity: float = 0.75
    min_trigger_specificity: float = 0.75
    min_balanced_accuracy: float = 0.75
    max_mean_policy_to_transferred_ratio: float = 0.95
    max_policy_harm_rate: float = 0.10
    max_mean_policy_regret: float = 0.05
    max_abs_mean_bias: float = 0.20
    min_coverage: float = 0.75
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07LGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07LDecision:
    passed: bool
    checks: tuple[V07LGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07LGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07l_gate(
    summary: V07LSummary,
    *,
    config: V07LGateConfig = V07LGateConfig(),
) -> V07LDecision:
    total_reps = config.replicates_per_world * len(V07L_WORLDS)
    checks = [
        _check(
            "replicates",
            summary.replicates == total_reps,
            summary.replicates,
            f"== {total_reps}",
        ),
        _check(
            "fit_count",
            summary.fit_count == 3 * total_reps,
            summary.fit_count,
            f"== {3 * total_reps}",
        ),
    ]

    below_worlds = ("strong_headroom", "threshold_below")
    above_worlds = ("threshold_above", "negligible_headroom")
    for world in V07L_WORLDS:
        row = summary.worlds[world]
        checks.append(
            _check(
                f"{world}:replicates",
                row.replicates == config.replicates_per_world,
                row.replicates,
                f"== {config.replicates_per_world}",
            )
        )
        if world in below_worlds:
            checks.append(
                _check(
                    f"{world}:trigger_rate",
                    row.trigger_rate >= config.min_trigger_rate_below_threshold,
                    row.trigger_rate,
                    f">= {config.min_trigger_rate_below_threshold}",
                )
            )
            checks.append(
                _check(
                    f"{world}:actual_material_headroom_rate",
                    row.actual_material_headroom_rate
                    >= config.min_actual_headroom_rate_below_threshold,
                    row.actual_material_headroom_rate,
                    f">= {config.min_actual_headroom_rate_below_threshold}",
                )
            )
        else:
            checks.append(
                _check(
                    f"{world}:trigger_rate",
                    row.trigger_rate <= config.max_trigger_rate_above_threshold,
                    row.trigger_rate,
                    f"<= {config.max_trigger_rate_above_threshold}",
                )
            )
            checks.append(
                _check(
                    f"{world}:actual_material_headroom_rate",
                    row.actual_material_headroom_rate
                    <= config.max_actual_headroom_rate_above_threshold,
                    row.actual_material_headroom_rate,
                    f"<= {config.max_actual_headroom_rate_above_threshold}",
                )
            )

        for target in V07B_TRUTH:
            checks.append(
                _check(
                    f"{world}:policy_bias:{target}",
                    abs(row.policy_mean_biases[target])
                    <= config.max_abs_mean_bias,
                    row.policy_mean_biases[target],
                    f"abs(mean bias) <= {config.max_abs_mean_bias}",
                )
            )
            checks.append(
                _check(
                    f"{world}:policy_coverage:{target}",
                    row.policy_coverages[target] >= config.min_coverage,
                    row.policy_coverages[target],
                    f">= {config.min_coverage}",
                )
            )

    checks.extend(
        [
            _check(
                "trigger_sensitivity",
                summary.trigger_sensitivity >= config.min_trigger_sensitivity,
                summary.trigger_sensitivity,
                f">= {config.min_trigger_sensitivity}",
            ),
            _check(
                "trigger_specificity",
                summary.trigger_specificity >= config.min_trigger_specificity,
                summary.trigger_specificity,
                f">= {config.min_trigger_specificity}",
            ),
            _check(
                "trigger_balanced_accuracy",
                summary.trigger_balanced_accuracy >= config.min_balanced_accuracy,
                summary.trigger_balanced_accuracy,
                f">= {config.min_balanced_accuracy}",
            ),
            _check(
                "mean_policy_to_transferred_ratio",
                summary.mean_policy_to_transferred_ratio
                <= config.max_mean_policy_to_transferred_ratio,
                summary.mean_policy_to_transferred_ratio,
                f"<= {config.max_mean_policy_to_transferred_ratio}",
            ),
            _check(
                "policy_harm_rate",
                summary.policy_harm_rate <= config.max_policy_harm_rate,
                summary.policy_harm_rate,
                f"<= {config.max_policy_harm_rate}",
            ),
            _check(
                "mean_policy_regret",
                summary.mean_policy_regret <= config.max_mean_policy_regret,
                summary.mean_policy_regret,
                f"<= {config.max_mean_policy_regret}",
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
    return V07LDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
