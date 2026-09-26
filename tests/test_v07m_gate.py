from esdm.validate.v07b_fixture import V07B_TRUTH
from esdm.validate.v07m_gate import V07MGateConfig, evaluate_v07m_gate
from esdm.validate.v07m_run import V07MSummary, V07MWorldSummary


def _world(world, expected):
    abstain = expected == "abstain"
    return V07MWorldSummary(
        world=world,
        expected_action=expected,
        replicates=16,
        fit_count=48,
        pilot_expected_action_rate=0.875,
        oracle_expected_action_rate=0.875,
        action_accuracy=0.875,
        policy_non_abstain_count=0 if abstain else 14,
        policy_abstain_rate=0.875 if abstain else 0.125,
        oracle_abstain_rate=0.875 if abstain else 0.125,
        policy_mean_biases=(
            {} if abstain else {target: 0.05 for target in V07B_TRUTH}
        ),
        policy_coverages=(
            {} if abstain else {target: 0.875 for target in V07B_TRUTH}
        ),
        mean_policy_to_transferred_ratio=None if abstain else 0.85,
        policy_harm_rate=None if abstain else 0.05,
        mean_policy_heldout_log_score=None if abstain else -1.0,
        total_divergences=0,
    )


def _summary(**overrides):
    worlds = {
        "adaptive_large_headroom": _world(
            "adaptive_large_headroom", "adaptive"
        ),
        "adaptive_absolute_rescue": _world(
            "adaptive_absolute_rescue", "adaptive"
        ),
        "transfer_adequate": _world(
            "transfer_adequate", "transferred"
        ),
        "abstain_inadequate": _world(
            "abstain_inadequate", "abstain"
        ),
    }
    values = dict(
        worlds=worlds,
        replicates=64,
        fit_count=192,
        action_correct_count=56,
        action_accuracy=0.875,
        oracle_abstain_count=14,
        pilot_abstain_true_positive=12,
        pilot_abstain_false_positive=4,
        pilot_abstain_true_negative=46,
        pilot_abstain_false_negative=2,
        abstain_sensitivity=12 / 14,
        non_abstain_specificity=46 / 50,
        mean_policy_to_transferred_ratio=0.88,
        policy_harm_rate=0.05,
        total_divergences=0,
    )
    values.update(overrides)
    return V07MSummary(**values)


def test_v07m_gate_passes_frozen_three_way_profile():
    decision = evaluate_v07m_gate(_summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)


def test_v07m_abstain_world_does_not_require_recovery_estimates():
    decision = evaluate_v07m_gate(_summary())

    names = {check.name for check in decision.checks}
    assert "abstain_inadequate:oracle_abstain_rate" in names
    assert not any(
        name.startswith("abstain_inadequate:policy_bias:")
        for name in names
    )
    assert not any(
        name.startswith("abstain_inadequate:policy_coverage:")
        for name in names
    )


def test_v07m_non_abstain_recovery_failure_fails_gate():
    summary = _summary()
    worlds = dict(summary.worlds)
    bad = worlds["transfer_adequate"]
    biases = dict(bad.policy_mean_biases)
    biases["sp.occupancy.gamma_logit"] = 0.21
    worlds["transfer_adequate"] = V07MWorldSummary(
        **{**bad.__dict__, "policy_mean_biases": biases}
    )
    summary = V07MSummary(**{**summary.__dict__, "worlds": worlds})

    decision = evaluate_v07m_gate(summary)

    assert not decision.passed
    check = next(
        row for row in decision.checks
        if row.name == "transfer_adequate:policy_bias:sp.occupancy.gamma_logit"
    )
    assert not check.passed


def test_v07m_gate_requires_safe_abstention_and_non_abstention():
    decision = evaluate_v07m_gate(
        _summary(abstain_sensitivity=0.70, non_abstain_specificity=0.70)
    )

    assert not decision.passed
    failed = {row.name for row in decision.checks if not row.passed}
    assert "abstain_sensitivity" in failed
    assert "non_abstain_specificity" in failed


def test_v07m_thresholds_are_inherited_not_configurable_from_summary():
    config = V07MGateConfig()
    assert config.min_expected_pilot_action_rate == 0.75
    assert config.min_expected_oracle_action_rate == 0.75
    assert config.min_action_accuracy == 0.75
    assert config.min_abstain_sensitivity == 0.75
    assert config.min_non_abstain_specificity == 0.75
    assert config.max_abs_mean_bias == 0.20
    assert config.min_coverage == 0.75
