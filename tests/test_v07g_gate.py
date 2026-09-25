from esdm.validate.v07b_fixture import V07B_TRUTH
from esdm.validate.v07g_gate import evaluate_v07g_gate
from esdm.validate.v07g_run import V07GSummary


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        optimized_lower_worst_sd_rate=0.875,
        mean_worst_sd_ratio=0.75,
        minimum_worst_sd_ratio=0.60,
        maximum_worst_sd_ratio=1.05,
        optimized_mean_biases={
            target: 0.02 for target in V07B_TRUTH
        },
        optimized_coverages={
            target: 0.875 for target in V07B_TRUTH
        },
        positive_heldout_gain_rate=0.625,
        mean_heldout_gain=0.01,
        minimum_heldout_gain=-0.05,
        total_divergences=0,
    )
    values.update(overrides)
    return V07GSummary(**values)


def test_v07g_gate_accepts_precision_improvement_with_recovery():
    decision = evaluate_v07g_gate(_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07g_gate_does_not_require_predictive_gain():
    decision = evaluate_v07g_gate(
        _summary(
            positive_heldout_gain_rate=0.0,
            mean_heldout_gain=-1.0,
            minimum_heldout_gain=-2.0,
        )
    )

    assert decision.passed


def test_v07g_gate_requires_replicated_precision_improvement():
    assert not evaluate_v07g_gate(
        _summary(optimized_lower_worst_sd_rate=0.6875)
    ).passed
    assert not evaluate_v07g_gate(
        _summary(mean_worst_sd_ratio=0.86)
    ).passed


def test_v07g_gate_requires_optimized_recovery_guardrail():
    target = next(iter(V07B_TRUTH))
    biased = dict(_summary().optimized_mean_biases)
    biased[target] = 0.16
    assert not evaluate_v07g_gate(
        _summary(optimized_mean_biases=biased)
    ).passed
