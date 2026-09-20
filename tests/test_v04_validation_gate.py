from dataclasses import replace

import pytest


def _passing_summary():
    from esdm.validate.v04_state_activity_gate import V04SemiSyntheticSummary

    return V04SemiSyntheticSummary(
        replicates=16,
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        extrapolation_integrity=True,
        activity_beta_precip_mean_bias=0.02,
        activity_beta_eastness_mean_bias=-0.03,
        state_beta_precip_mean_bias=0.01,
        state_beta_eastness_mean_bias=-0.02,
        activity_beta_precip_coverage=0.875,
        activity_beta_eastness_coverage=0.8125,
        state_beta_precip_coverage=0.875,
        state_beta_eastness_coverage=0.75,
        activity_positive_gain_rate=0.8125,
        mean_activity_gain=0.02,
        state_positive_gain_rate=0.8125,
        mean_state_gain=0.015,
        total_divergences=3,
        fit_count=48,
    )


def test_v04_gate_thresholds_match_frozen_document():
    from esdm.validate.v04_state_activity_gate import V04GateConfig

    config = V04GateConfig()
    assert config.replicates == 16
    assert config.fit_count == 48
    assert config.max_abs_bias == 0.15
    assert config.min_coverage == 0.75
    assert config.min_positive_gain_rate == 0.75
    assert config.min_mean_heldout_gain == 0.005
    assert config.max_mean_divergences_per_fit == 0.10


def test_v04_gate_accepts_complete_frozen_evidence():
    from esdm.validate.v04_state_activity_gate import evaluate_v04_gate

    decision = evaluate_v04_gate(_passing_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)
    assert len(decision.checks) == 21


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
def test_v04_gate_boolean_terms_fail_independently(field):
    from esdm.validate.v04_state_activity_gate import evaluate_v04_gate

    decision = evaluate_v04_gate(replace(_passing_summary(), **{field: False}))
    assert decision.passed is False
    assert any(check.name == field and not check.passed for check in decision.checks)


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    [
        ({"replicates": 15}, "replicates"),
        ({"fit_count": 47}, "fit_count"),
        ({"activity_beta_precip_mean_bias": 0.151}, "activity_beta_precip_bias"),
        ({"activity_beta_eastness_mean_bias": -0.151}, "activity_beta_eastness_bias"),
        ({"state_beta_precip_mean_bias": 0.151}, "state_beta_precip_bias"),
        ({"state_beta_eastness_mean_bias": -0.151}, "state_beta_eastness_bias"),
        ({"activity_beta_precip_coverage": 0.749}, "activity_beta_precip_coverage"),
        ({"activity_beta_eastness_coverage": 0.749}, "activity_beta_eastness_coverage"),
        ({"state_beta_precip_coverage": 0.749}, "state_beta_precip_coverage"),
        ({"state_beta_eastness_coverage": 0.749}, "state_beta_eastness_coverage"),
        ({"activity_positive_gain_rate": 0.749}, "activity_positive_gain_rate"),
        ({"mean_activity_gain": 0.0049}, "activity_mean_gain"),
        ({"state_positive_gain_rate": 0.749}, "state_positive_gain_rate"),
        ({"mean_state_gain": 0.0049}, "state_mean_gain"),
        ({"total_divergences": 5}, "mean_divergences_per_fit"),
    ],
)
def test_v04_gate_numeric_terms_fail_independently(changes, failed_check):
    from esdm.validate.v04_state_activity_gate import evaluate_v04_gate

    decision = evaluate_v04_gate(replace(_passing_summary(), **changes))
    assert decision.passed is False
    assert any(check.name == failed_check and not check.passed for check in decision.checks)
