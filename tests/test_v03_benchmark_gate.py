import pytest


def test_v03_promotion_requires_all_four_axes():
    from esdm.validate.benchmark import V03GateEvidence, V03GateThresholds, evaluate_v03_promotion

    decision = evaluate_v03_promotion(
        V03GateEvidence(
            sbc_total_variation=0.06,
            knockout_abs_effect=0.03,
            wrong_effort_abs_bias=0.45,
            hidden_driver_abs_bias=0.32,
            restrained_under_misspecification=True,
        ),
        V03GateThresholds(
            max_sbc_total_variation=0.10,
            max_knockout_abs_effect=0.10,
            min_wrong_effort_abs_bias=0.20,
            min_hidden_driver_abs_bias=0.20,
        ),
    )

    assert decision.promote is True
    assert decision.axes == {
        "calibration": True,
        "knockout_recovery": True,
        "misspecification_sensitivity": True,
        "claim_restraint": True,
    }


def test_v03_promotion_fails_when_sbc_passes_but_claim_restraint_fails():
    from esdm.validate.benchmark import V03GateEvidence, V03GateThresholds, evaluate_v03_promotion

    decision = evaluate_v03_promotion(
        V03GateEvidence(
            sbc_total_variation=0.04,
            knockout_abs_effect=0.02,
            wrong_effort_abs_bias=0.50,
            hidden_driver_abs_bias=0.40,
            restrained_under_misspecification=False,
        ),
        V03GateThresholds(),
    )

    assert decision.axes["calibration"] is True
    assert decision.axes["claim_restraint"] is False
    assert decision.promote is False


def test_v03_gate_rejects_nonfinite_evidence():
    from esdm.validate.benchmark import V03GateEvidence

    with pytest.raises(ValueError):
        V03GateEvidence(
            sbc_total_variation=float("nan"),
            knockout_abs_effect=0.0,
            wrong_effort_abs_bias=0.3,
            hidden_driver_abs_bias=0.3,
            restrained_under_misspecification=True,
        )
