from __future__ import annotations

from esdm.validate.tr1_gate import evaluate_tr1_gate
from esdm.validate.tr1_trait_transfer import TR1WorldSummary


def _positive(**overrides):
    values = dict(
        world="positive",
        replicates=32,
        mean_gain=0.08,
        minimum_gain=-0.01,
        maximum_gain=0.14,
        positive_gain_rate=0.875,
        material_gain_count=30,
        material_gain_threshold=0.01,
        mean_fitted_trait_coefficient=1.02,
        mean_trait_coefficient_bias=0.02,
    )
    values.update(overrides)
    return TR1WorldSummary(**values)


def _null(**overrides):
    values = dict(
        world="null",
        replicates=32,
        mean_gain=-0.001,
        minimum_gain=-0.04,
        maximum_gain=0.018,
        positive_gain_rate=0.4375,
        material_gain_count=4,
        material_gain_threshold=0.01,
        mean_fitted_trait_coefficient=0.03,
        mean_trait_coefficient_bias=0.03,
    )
    values.update(overrides)
    return TR1WorldSummary(**values)


def test_tr1_gate_passes_only_joint_positive_and_specificity_profile():
    decision = evaluate_tr1_gate(_positive(), _null())

    assert decision.passed
    assert len(decision.checks) == 8
    assert all(check.passed for check in decision.checks)


def test_tr1_gate_fails_when_positive_transfer_is_too_weak():
    decision = evaluate_tr1_gate(_positive(mean_gain=0.029), _null())

    assert not decision.passed
    check = next(row for row in decision.checks if row.name == "positive_mean_gain")
    assert not check.passed


def test_tr1_gate_fails_specificity_if_material_null_count_exceeds_frozen_limit():
    decision = evaluate_tr1_gate(_positive(), _null(material_gain_count=9))

    assert not decision.passed
    check = next(
        row for row in decision.checks
        if row.name == "null_material_gain_count"
    )
    assert check.criterion == "<= 8"
    assert not check.passed


def test_tr1_gate_fails_specificity_if_null_mean_gain_exceeds_limit():
    decision = evaluate_tr1_gate(_positive(), _null(mean_gain=0.006))

    assert not decision.passed
    check = next(row for row in decision.checks if row.name == "null_mean_gain")
    assert not check.passed
