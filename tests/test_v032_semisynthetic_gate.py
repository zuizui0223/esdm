from dataclasses import replace

import pytest


def _passing_summary():
    from esdm.validate.v032_semisynthetic_gate import V032SemiSyntheticSummary

    return V032SemiSyntheticSummary(
        replicates=20,
        positive_structural_pass=True,
        positive_practical_pass=True,
        negative_structural_pass=True,
        negative_practical_refused=True,
        extrapolation_integrity=True,
        beta_precip_mean_bias=0.02,
        gamma_precip_mean_bias=-0.03,
        beta_eastness_mean_bias=0.01,
        beta_precip_coverage=0.85,
        gamma_precip_coverage=0.80,
        beta_eastness_coverage=0.90,
        positive_gain_rate=0.90,
        mean_heldout_gain=0.04,
        total_divergences=2,
        fit_count=40,
    )


def test_v032_gate_accepts_only_complete_positive_and_negative_control_evidence():
    from esdm.validate.v032_semisynthetic_gate import evaluate_v032_semisynthetic_gate

    decision = evaluate_v032_semisynthetic_gate(_passing_summary())
    assert decision.passed is True
    assert all(check.passed for check in decision.checks)


@pytest.mark.parametrize(
    "field",
    [
        "positive_structural_pass",
        "positive_practical_pass",
        "negative_structural_pass",
        "negative_practical_refused",
        "extrapolation_integrity",
    ],
)
def test_v032_gate_boolean_conjunction_terms_fail_independently(field):
    from esdm.validate.v032_semisynthetic_gate import evaluate_v032_semisynthetic_gate

    summary = replace(_passing_summary(), **{field: False})
    decision = evaluate_v032_semisynthetic_gate(summary)
    assert decision.passed is False
    assert any(check.name == field and not check.passed for check in decision.checks)


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    [
        ({"replicates": 19}, "replicates"),
        ({"beta_precip_mean_bias": 0.151}, "beta_precip_bias"),
        ({"gamma_precip_mean_bias": -0.151}, "gamma_precip_bias"),
        ({"beta_eastness_mean_bias": 0.151}, "beta_eastness_bias"),
        ({"beta_precip_coverage": 0.74}, "beta_precip_coverage"),
        ({"gamma_precip_coverage": 0.74}, "gamma_precip_coverage"),
        ({"beta_eastness_coverage": 0.74}, "beta_eastness_coverage"),
        ({"positive_gain_rate": 0.79}, "heldout_positive_gain_rate"),
        ({"mean_heldout_gain": 0.009}, "heldout_mean_gain"),
        ({"total_divergences": 5}, "mean_divergences_per_fit"),
    ],
)
def test_v032_gate_numeric_terms_fail_independently(changes, failed_check):
    from esdm.validate.v032_semisynthetic_gate import evaluate_v032_semisynthetic_gate

    decision = evaluate_v032_semisynthetic_gate(replace(_passing_summary(), **changes))
    assert decision.passed is False
    assert any(check.name == failed_check and not check.passed for check in decision.checks)


def test_v032_gate_thresholds_match_frozen_document():
    from esdm.validate.v032_semisynthetic_gate import V032SemiSyntheticGateConfig

    config = V032SemiSyntheticGateConfig()
    assert config.replicates == 20
    assert config.max_abs_bias == 0.15
    assert config.min_coverage == 0.75
    assert config.min_positive_gain_rate == 0.80
    assert config.min_mean_heldout_gain == 0.01
    assert config.max_mean_divergences_per_fit == 0.10
