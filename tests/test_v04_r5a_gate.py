from dataclasses import replace


def _passing_summary():
    from esdm.validate.v04_r5a_gate import V04R5AQualificationSummary

    return V04R5AQualificationSummary(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        annotated_context_count=432,
        calibrated_context_count=432,
        state_calibration_context_count=432,
        state_calibration_expected_labels=432.0,
        state_calibration_heldout_context_count=0,
        r4_annotated_geometry_preserved=True,
        state_only_contract_preserved=True,
    )


def test_r5a_mechanical_gate_requires_complete_qualification():
    from esdm.validate.v04_r5a_gate import evaluate_v04_r5a_qualification

    decision = evaluate_v04_r5a_qualification(_passing_summary())

    assert decision.passed is True
    assert len(decision.checks) == 12
    assert all(check.passed for check in decision.checks)


def test_r5a_each_gate_term_is_required():
    from esdm.validate.v04_r5a_gate import evaluate_v04_r5a_qualification

    cases = {
        "positive_structural_pass": False,
        "positive_practical_pass": False,
        "sparse_structural_pass": False,
        "sparse_practical_refused": False,
        "unknown_detection_refused": False,
        "annotated_context_count": 431,
        "calibrated_context_count": 431,
        "state_calibration_context_count": 431,
        "state_calibration_expected_labels": 431.0,
        "state_calibration_heldout_context_count": 1,
        "r4_annotated_geometry_preserved": False,
        "state_only_contract_preserved": False,
    }
    for field, value in cases.items():
        decision = evaluate_v04_r5a_qualification(
            replace(_passing_summary(), **{field: value})
        )
        assert decision.passed is False
        assert any(
            check.name == field and not check.passed
            for check in decision.checks
        )
