from dataclasses import replace

import pytest


TARGETS = (
    "sp.suitability.beta_precip",
    "stream.opportunistic.gamma_precip",
    "stream.opportunistic.gamma_season",
    "stream.opportunistic.gamma_hour",
    "stream.opportunistic.detection_intercept",
    "sp.activity.activity_beta_precip",
    "sp.activity.activity_beta_eastness",
    "sp.activity.activity_beta_season",
    "sp.activity.activity_beta_hour",
    "sp.state.beta_foraging_precip",
    "sp.state.beta_foraging_eastness",
    "sp.state.beta_foraging_season",
    "sp.state.beta_foraging_hour",
)


def _passing_summary():
    from esdm.validate.v04_r2_gate import V04R2Summary

    return V04R2Summary(
        replicates=16,
        fit_count=48,
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        extrapolation_integrity=True,
        mean_biases={target: 0.02 for target in TARGETS},
        coverages={target: 0.8125 for target in TARGETS},
        activity_positive_gain_rate=0.8125,
        mean_activity_gain=0.02,
        state_positive_gain_rate=0.8125,
        mean_state_gain=0.015,
        total_divergences=3,
    )


def test_r2_gate_config_matches_frozen_document():
    from esdm.validate.v04_r2_gate import V04R2GateConfig

    config = V04R2GateConfig()
    assert config.replicates == 16
    assert config.fit_count == 48
    assert config.max_abs_bias == 0.18
    assert config.min_coverage == 0.75
    assert config.min_positive_gain_rate == 0.75
    assert config.min_mean_heldout_gain == 0.005
    assert config.max_mean_divergences_per_fit == 0.10


def test_r2_gate_accepts_only_complete_frozen_conjunction():
    from esdm.validate.v04_r2_gate import evaluate_v04_r2_gate

    decision = evaluate_v04_r2_gate(_passing_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)
    assert len(decision.checks) == 39


@pytest.mark.parametrize(
    "field",
    [
        "positive_structural_pass",
        "positive_practical_pass",
        "sparse_structural_pass",
        "sparse_practical_refused",
        "unknown_detection_refused",
        "extrapolation_integrity",
    ],
)
def test_r2_boolean_terms_fail_independently(field):
    from esdm.validate.v04_r2_gate import evaluate_v04_r2_gate

    decision = evaluate_v04_r2_gate(
        replace(_passing_summary(), **{field: False})
    )
    assert decision.passed is False
    assert any(check.name == field and not check.passed for check in decision.checks)


def test_r2_recovery_bias_and_coverage_fail_per_target():
    from esdm.validate.v04_r2_gate import evaluate_v04_r2_gate

    for target in TARGETS:
        summary = _passing_summary()
        biases = dict(summary.mean_biases)
        biases[target] = -0.181
        decision = evaluate_v04_r2_gate(
            replace(summary, mean_biases=biases)
        )
        assert decision.passed is False
        assert any(
            check.name == f"{target}.bias" and not check.passed
            for check in decision.checks
        )

        summary = _passing_summary()
        coverages = dict(summary.coverages)
        coverages[target] = 0.749
        decision = evaluate_v04_r2_gate(
            replace(summary, coverages=coverages)
        )
        assert decision.passed is False
        assert any(
            check.name == f"{target}.coverage" and not check.passed
            for check in decision.checks
        )


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    [
        ({"replicates": 15}, "replicates"),
        ({"fit_count": 47}, "fit_count"),
        ({"activity_positive_gain_rate": 0.749}, "activity_positive_gain_rate"),
        ({"mean_activity_gain": 0.0049}, "activity_mean_gain"),
        ({"state_positive_gain_rate": 0.749}, "state_positive_gain_rate"),
        ({"mean_state_gain": 0.0049}, "state_mean_gain"),
        ({"total_divergences": 5}, "mean_divergences_per_fit"),
    ],
)
def test_r2_numeric_nonrecovery_terms_fail_independently(changes, failed_check):
    from esdm.validate.v04_r2_gate import evaluate_v04_r2_gate

    decision = evaluate_v04_r2_gate(
        replace(_passing_summary(), **changes)
    )
    assert decision.passed is False
    assert any(
        check.name == failed_check and not check.passed
        for check in decision.checks
    )


def test_r2_gate_rejects_missing_or_extra_recovery_targets():
    from esdm.validate.v04_r2_gate import evaluate_v04_r2_gate

    summary = _passing_summary()
    biases = dict(summary.mean_biases)
    biases.pop(TARGETS[0])
    with pytest.raises(ValueError, match="recovery targets"):
        evaluate_v04_r2_gate(replace(summary, mean_biases=biases))

    summary = _passing_summary()
    coverages = dict(summary.coverages)
    coverages["extra"] = 1.0
    with pytest.raises(ValueError, match="recovery targets"):
        evaluate_v04_r2_gate(replace(summary, coverages=coverages))
