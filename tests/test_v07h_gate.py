from esdm.validate.v07b_fixture import V07B_TRUTH
from esdm.validate.v07h_gate import evaluate_v07h_gate
from esdm.validate.v07h_run import V07HSummary


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        selected_lower_worst_sd_rate=0.875,
        mean_worst_sd_ratio=0.80,
        minimum_worst_sd_ratio=0.65,
        maximum_worst_sd_ratio=1.05,
        selected_mean_biases={target: 0.02 for target in V07B_TRUTH},
        selected_coverages={target: 0.875 for target in V07B_TRUTH},
        positive_heldout_gain_rate=0.5,
        mean_heldout_gain=0.0,
        minimum_heldout_gain=-0.2,
        total_divergences=0,
    )
    values.update(overrides)
    return V07HSummary(**values)


def test_v07h_gate_accepts_expected_count_matched_precision_gain():
    decision = evaluate_v07h_gate(_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07h_gate_does_not_promote_prediction():
    assert evaluate_v07h_gate(
        _summary(
            positive_heldout_gain_rate=0.0,
            mean_heldout_gain=-1.0,
            minimum_heldout_gain=-2.0,
        )
    ).passed


def test_v07h_gate_requires_precision_and_recovery():
    assert not evaluate_v07h_gate(
        _summary(selected_lower_worst_sd_rate=0.6875)
    ).passed
    assert not evaluate_v07h_gate(
        _summary(mean_worst_sd_ratio=0.91)
    ).passed

    target = next(iter(V07B_TRUTH))
    bias = dict(_summary().selected_mean_biases)
    bias[target] = 0.16
    assert not evaluate_v07h_gate(
        _summary(selected_mean_biases=bias)
    ).passed
