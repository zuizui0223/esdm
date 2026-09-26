from __future__ import annotations

from esdm.validate.v07b_fixture import V07B_TRUTH
from esdm.validate.v07l_gate import V07LGateConfig, evaluate_v07l_gate
from esdm.validate.v07l_run import V07LSummary, V07LWorldSummary


def _world(
    world,
    *,
    trigger_rate,
    actual_rate,
    policy_ratio,
    harm_rate=0.0,
    regret=0.01,
):
    return V07LWorldSummary(
        world=world,
        replicates=16,
        fit_count=48,
        trigger_rate=trigger_rate,
        actual_material_headroom_rate=actual_rate,
        trigger_correct_rate=0.875,
        mean_predicted_ratio=0.75 if trigger_rate > 0.5 else 0.90,
        mean_actual_ratio=0.72 if actual_rate > 0.5 else 0.91,
        mean_policy_to_transferred_ratio=policy_ratio,
        policy_harm_rate=harm_rate,
        mean_policy_regret=regret,
        policy_mean_biases={target: 0.02 for target in V07B_TRUTH},
        policy_coverages={target: 0.875 for target in V07B_TRUTH},
        mean_adaptive_minus_transferred_heldout_gain=0.0,
        total_divergences=0,
    )


def _passing_summary():
    worlds = {
        "strong_headroom": _world(
            "strong_headroom", trigger_rate=0.875, actual_rate=0.875, policy_ratio=0.72
        ),
        "threshold_below": _world(
            "threshold_below", trigger_rate=0.75, actual_rate=0.75, policy_ratio=0.82
        ),
        "threshold_above": _world(
            "threshold_above", trigger_rate=0.25, actual_rate=0.25, policy_ratio=0.97
        ),
        "negligible_headroom": _world(
            "negligible_headroom", trigger_rate=0.0, actual_rate=0.0, policy_ratio=1.0
        ),
    }
    return V07LSummary(
        worlds=worlds,
        replicates=64,
        fit_count=192,
        trigger_true_positive=24,
        trigger_false_positive=4,
        trigger_true_negative=28,
        trigger_false_negative=8,
        trigger_sensitivity=0.75,
        trigger_specificity=0.875,
        trigger_balanced_accuracy=0.8125,
        mean_policy_to_transferred_ratio=0.88,
        policy_harm_rate=0.046875,
        mean_policy_regret=0.03,
        total_divergences=0,
    )


def test_v07l_gate_passes_selective_policy_profile():
    decision = evaluate_v07l_gate(_passing_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)
    assert V07LGateConfig().min_balanced_accuracy == 0.75
    assert V07LGateConfig().max_policy_harm_rate == 0.10


def test_v07l_gate_rejects_excess_triggering_above_threshold():
    summary = _passing_summary()
    worlds = dict(summary.worlds)
    worlds["threshold_above"] = _world(
        "threshold_above",
        trigger_rate=0.50,
        actual_rate=0.25,
        policy_ratio=0.95,
    )
    broken = V07LSummary(
        worlds=worlds,
        replicates=summary.replicates,
        fit_count=summary.fit_count,
        trigger_true_positive=summary.trigger_true_positive,
        trigger_false_positive=summary.trigger_false_positive,
        trigger_true_negative=summary.trigger_true_negative,
        trigger_false_negative=summary.trigger_false_negative,
        trigger_sensitivity=summary.trigger_sensitivity,
        trigger_specificity=summary.trigger_specificity,
        trigger_balanced_accuracy=summary.trigger_balanced_accuracy,
        mean_policy_to_transferred_ratio=summary.mean_policy_to_transferred_ratio,
        policy_harm_rate=summary.policy_harm_rate,
        mean_policy_regret=summary.mean_policy_regret,
        total_divergences=summary.total_divergences,
    )

    decision = evaluate_v07l_gate(broken)

    assert not decision.passed
    failed = [row.name for row in decision.checks if not row.passed]
    assert "threshold_above:trigger_rate" in failed


def test_v07l_gate_rejects_policy_harm_even_with_good_classification():
    summary = _passing_summary()
    broken = V07LSummary(
        worlds=summary.worlds,
        replicates=summary.replicates,
        fit_count=summary.fit_count,
        trigger_true_positive=summary.trigger_true_positive,
        trigger_false_positive=summary.trigger_false_positive,
        trigger_true_negative=summary.trigger_true_negative,
        trigger_false_negative=summary.trigger_false_negative,
        trigger_sensitivity=summary.trigger_sensitivity,
        trigger_specificity=summary.trigger_specificity,
        trigger_balanced_accuracy=summary.trigger_balanced_accuracy,
        mean_policy_to_transferred_ratio=summary.mean_policy_to_transferred_ratio,
        policy_harm_rate=0.125,
        mean_policy_regret=summary.mean_policy_regret,
        total_divergences=summary.total_divergences,
    )

    decision = evaluate_v07l_gate(broken)

    assert not decision.passed
    failed = [row.name for row in decision.checks if not row.passed]
    assert "policy_harm_rate" in failed
