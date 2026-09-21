from dataclasses import replace


def _passing_summary():
    from esdm.validate.v04_r3a_gate import V04R3AQualificationSummary

    return V04R3AQualificationSummary(
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        annotated_context_count=432,
        annotated_space_count=36,
        annotated_time_count=12,
        calibrated_context_count=432,
        r2_prefix_preserved=True,
    )


def test_r3a_mechanical_gate_accepts_only_complete_design_qualification():
    from esdm.validate.v04_r3a_gate import evaluate_v04_r3a_qualification

    decision = evaluate_v04_r3a_qualification(_passing_summary())

    assert decision.passed is True
    assert len(decision.checks) == 10
    assert all(check.passed for check in decision.checks)


def test_r3a_each_term_is_required():
    from esdm.validate.v04_r3a_gate import evaluate_v04_r3a_qualification

    cases = {
        "positive_structural_pass": False,
        "positive_practical_pass": False,
        "sparse_structural_pass": False,
        "sparse_practical_refused": False,
        "unknown_detection_refused": False,
        "annotated_context_count": 431,
        "annotated_space_count": 35,
        "annotated_time_count": 11,
        "calibrated_context_count": 431,
        "r2_prefix_preserved": False,
    }
    for field, value in cases.items():
        decision = evaluate_v04_r3a_qualification(
            replace(_passing_summary(), **{field: value})
        )
        assert decision.passed is False
        assert any(
            check.name == field and not check.passed
            for check in decision.checks
        )


def test_r3a_gate_uses_exact_budget_criteria():
    from esdm.validate.v04_r3a_gate import evaluate_v04_r3a_qualification

    decision = evaluate_v04_r3a_qualification(_passing_summary())
    by_name = {check.name: check for check in decision.checks}

    assert by_name["annotated_context_count"].criterion == "== 432"
    assert by_name["annotated_space_count"].criterion == "== 36"
    assert by_name["annotated_time_count"].criterion == "== 12"
    assert by_name["calibrated_context_count"].criterion == "== 432"
