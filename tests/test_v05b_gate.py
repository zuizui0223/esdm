from esdm.validate.v05b_run import V05BSummary


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        mean_beta=0.02,
        zero_coverage=0.875,
        nonzero_interval_rate=0.125,
        positive_interval_rate=0.0625,
        heldout_positive_gain_rate=0.25,
        heldout_material_gain_rate=0.125,
        mean_heldout_gain=-0.01,
        total_divergences=0,
    )
    values.update(overrides)
    return V05BSummary(**values)


def test_v05b_gate_reuses_v05a_null_refusal_thresholds():
    from esdm.validate.v05b_gate import evaluate_v05b_gate

    decision = evaluate_v05b_gate(_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_v05b_gate_rejects_spurious_hidden_driver_interaction():
    from esdm.validate.v05b_gate import evaluate_v05b_gate

    assert evaluate_v05b_gate(_summary(mean_beta=0.12)).passed is False
    assert evaluate_v05b_gate(
        _summary(heldout_material_gain_rate=0.3125)
    ).passed is False
