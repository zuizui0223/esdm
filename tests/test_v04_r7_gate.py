from esdm.validate.v04_r7_run import V04R7Summary


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        all_shared_base_data_equal=True,
        direct_expected_labels=432.0,
        passive_expected_labels=432.0,
        mean_direct_realized_labels=431.0,
        mean_passive_realized_labels=433.0,
        heldout_positive_gain_rate=0.875,
        mean_heldout_gain=0.01,
        state_error_positive_gain_rate=0.875,
        mean_state_error_gain=0.02,
        total_divergences=0,
    )
    values.update(overrides)
    return V04R7Summary(**values)


def test_r7_gate_accepts_budget_matched_information_advantage():
    from esdm.validate.v04_r7_gate import evaluate_v04_r7_gate

    decision = evaluate_v04_r7_gate(_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_r7_gate_requires_predictive_and_recovery_advantage():
    from esdm.validate.v04_r7_gate import evaluate_v04_r7_gate

    assert evaluate_v04_r7_gate(
        _summary(mean_heldout_gain=0.004)
    ).passed is False
    assert evaluate_v04_r7_gate(
        _summary(mean_state_error_gain=-0.001)
    ).passed is False
