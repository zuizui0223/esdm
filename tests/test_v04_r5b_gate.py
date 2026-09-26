from types import SimpleNamespace


def _qualification():
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


def _outcome():
    from esdm.validate.v04_r2_gate import R2_RECOVERY_TRUTH, V04R2Summary

    return V04R2Summary(
        replicates=16,
        fit_count=48,
        positive_structural_pass=True,
        positive_practical_pass=True,
        sparse_structural_pass=True,
        sparse_practical_refused=True,
        unknown_detection_refused=True,
        extrapolation_integrity=True,
        mean_biases={target: 0.0 for target in R2_RECOVERY_TRUTH},
        coverages={target: 1.0 for target in R2_RECOVERY_TRUTH},
        activity_positive_gain_rate=1.0,
        mean_activity_gain=0.02,
        state_positive_gain_rate=1.0,
        mean_state_gain=0.02,
        total_divergences=0,
    )


def test_r5b_combined_gate_requires_qualification_and_outcome():
    from esdm.validate.v04_r5b_gate import evaluate_v04_r5b_gate

    decision = evaluate_v04_r5b_gate(_qualification(), _outcome())

    assert decision.passed is True
    assert decision.qualification_passed is True
    assert decision.outcome_passed is True
