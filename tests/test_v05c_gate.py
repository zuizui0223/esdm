from esdm.validate.v05c_run import V05CSummary, V05CWorldSummary


def _summary(**null_overrides):
    true = V05CWorldSummary(
        world="interaction_event",
        replicates=16,
        beta_positive_rate=0.875,
        event_support_rate=0.875,
        realized_claim_rate=0.875,
        mean_event_probability=0.24,
        event_probability_bias=-0.01,
        event_probability_coverage=0.875,
        mean_training_event_count=40.0,
        total_divergences=0,
    )
    null_values = dict(
        world="hidden_driver_null",
        replicates=16,
        beta_positive_rate=1.0,
        event_support_rate=0.125,
        realized_claim_rate=0.125,
        mean_event_probability=0.012,
        event_probability_bias=0.007,
        event_probability_coverage=0.875,
        mean_training_event_count=1.0,
        total_divergences=0,
    )
    null_values.update(null_overrides)
    return V05CSummary(
        worlds={
            "interaction_event": true,
            "hidden_driver_null": V05CWorldSummary(**null_values),
        },
        total_fits=32,
        total_divergences=0,
    )


def test_v05c_gate_allows_hidden_beta_false_positive_but_blocks_realized_claim():
    from esdm.validate.v05c_gate import evaluate_v05c_gate

    decision = evaluate_v05c_gate(_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


def test_v05c_gate_rejects_hidden_null_event_promotion():
    from esdm.validate.v05c_gate import evaluate_v05c_gate

    assert evaluate_v05c_gate(
        _summary(event_support_rate=0.3125)
    ).passed is False
    assert evaluate_v05c_gate(
        _summary(realized_claim_rate=0.3125)
    ).passed is False
