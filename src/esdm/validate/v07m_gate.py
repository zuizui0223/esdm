"""Mechanical gate for frozen v0.7m three-way calibration policy."""
from __future__ import annotations

from dataclasses import dataclass

from .v07b_fixture import V07B_TRUTH
from .v07m_fixture import V07M_WORLDS
from .v07m_policy import V07M_EXPECTED_ACTIONS
from .v07m_run import V07MSummary


@dataclass(frozen=True, slots=True)
class V07MGateConfig:
    replicates_per_world: int = 16
    min_expected_pilot_action_rate: float = 0.75
    min_expected_oracle_action_rate: float = 0.75
    min_action_accuracy: float = 0.75
    min_abstain_sensitivity: float = 0.75
    min_non_abstain_specificity: float = 0.75
    min_non_abstain_count_per_recovery_world: int = 12
    max_abs_mean_bias: float = 0.20
    min_coverage: float = 0.75
    max_mean_policy_to_transferred_ratio: float = 0.95
    max_policy_harm_rate: float = 0.10
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V07MGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V07MDecision:
    passed: bool
    checks: tuple[V07MGateCheck, ...]


def _check(name, passed, observed, criterion):
    return V07MGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v07m_gate(
    summary: V07MSummary,
    *,
    config: V07MGateConfig = V07MGateConfig(),
) -> V07MDecision:
    total_reps = config.replicates_per_world * len(V07M_WORLDS)
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

    for world in V07M_WORLDS:
        row = summary.worlds[world]
        expected = V07M_EXPECTED_ACTIONS[world]
        checks.extend(
            [
                _check(
                    f"{world}:replicates",
                    row.replicates == config.replicates_per_world,
                    row.replicates,
                    f"== {config.replicates_per_world}",
                ),
                _check(
                    f"{world}:pilot_expected_action_rate",
                    row.pilot_expected_action_rate
                    >= config.min_expected_pilot_action_rate,
                    row.pilot_expected_action_rate,
                    f">= {config.min_expected_pilot_action_rate}",
                ),
                _check(
                    f"{world}:oracle_expected_action_rate",
                    row.oracle_expected_action_rate
                    >= config.min_expected_oracle_action_rate,
                    row.oracle_expected_action_rate,
                    f">= {config.min_expected_oracle_action_rate}",
                ),
            ]
        )

        if expected != "abstain":
            checks.append(
                _check(
                    f"{world}:policy_non_abstain_count",
                    row.policy_non_abstain_count
                    >= config.min_non_abstain_count_per_recovery_world,
                    row.policy_non_abstain_count,
                    f">= {config.min_non_abstain_count_per_recovery_world}",
                )
            )
            for target in V07B_TRUTH:
                checks.extend(
                    [
                        _check(
                            f"{world}:policy_bias:{target}",
                            abs(row.policy_mean_biases[target])
                            <= config.max_abs_mean_bias,
                            row.policy_mean_biases[target],
                            f"abs(mean bias) <= {config.max_abs_mean_bias}",
                        ),
                        _check(
                            f"{world}:policy_coverage:{target}",
                            row.policy_coverages[target] >= config.min_coverage,
                            row.policy_coverages[target],
                            f">= {config.min_coverage}",
                        ),
                    ]
                )
        else:
            checks.append(
                _check(
                    f"{world}:oracle_abstain_rate",
                    row.oracle_abstain_rate
                    >= config.min_expected_oracle_action_rate,
                    row.oracle_abstain_rate,
                    f">= {config.min_expected_oracle_action_rate}",
                )
            )

    checks.extend(
        [
            _check(
                "action_accuracy",
                summary.action_accuracy >= config.min_action_accuracy,
                summary.action_accuracy,
                f">= {config.min_action_accuracy}",
            ),
            _check(
                "abstain_sensitivity",
                summary.abstain_sensitivity >= config.min_abstain_sensitivity,
                summary.abstain_sensitivity,
                f">= {config.min_abstain_sensitivity}",
            ),
            _check(
                "non_abstain_specificity",
                summary.non_abstain_specificity
                >= config.min_non_abstain_specificity,
                summary.non_abstain_specificity,
                f">= {config.min_non_abstain_specificity}",
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

    return V07MDecision(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
