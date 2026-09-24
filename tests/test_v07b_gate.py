from esdm.validate.v07b_gate import (
    V07BGateConfig,
    evaluate_v07b_gate,
)
from esdm.validate.v07b_fixture import V07B_RECOVERY_TRUTH
from esdm.validate.v07b_qualification import V07BQualification
from esdm.validate.v07b_run import V07BSummary


def _qualification():
    return V07BQualification(
        positive_structural_pass=True,
        positive_practical_pass=True,
        joint_only_refusal_pass=True,
        positive_evidence={},
        refusal_evidence={},
    )


def _summary(**overrides):
    values = dict(
        replicates=16,
        fit_count=32,
        mean_biases={target: 0.01 for target in V07B_RECOVERY_TRUTH},
        coverages={target: 0.875 for target in V07B_RECOVERY_TRUTH},
        positive_gain_rate=0.875,
        mean_gain=0.10,
        minimum_gain=-0.02,
        total_divergences=0,
        mean_full_heldout_log_score=-1.20,
        mean_knockout_heldout_log_score=-1.30,
    )
    values.update(overrides)
    return V07BSummary(**values)


def test_v07b_gate_passes_complete_frozen_profile():
    decision = evaluate_v07b_gate(_qualification(), _summary())

    assert decision.passed
    assert all(check.passed for check in decision.checks)
    assert any(check.name == "absolute_score_serialization" for check in decision.checks)


def test_v07b_gate_requires_absolute_score_identity():
    decision = evaluate_v07b_gate(
        _qualification(),
        _summary(mean_full_heldout_log_score=-1.21),
    )

    assert not decision.passed
    check = next(
        row for row in decision.checks
        if row.name == "absolute_score_serialization"
    )
    assert not check.passed


def test_v07b_gate_does_not_require_every_replicate_positive():
    summary = _summary(
        positive_gain_rate=0.75,
        minimum_gain=-0.40,
        mean_gain=0.02,
        mean_full_heldout_log_score=-1.28,
        mean_knockout_heldout_log_score=-1.30,
    )
    decision = evaluate_v07b_gate(_qualification(), summary)

    assert decision.passed
    assert V07BGateConfig().min_positive_gain_rate == 0.75
