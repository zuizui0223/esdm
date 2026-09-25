import pytest

from esdm.validate.v05a_gate import V05AGateConfig
from esdm.validate.v05a_qualification import V05AQualification
from esdm.validate.v05f_gate import evaluate_v05f_gate
from esdm.validate.v05f_run import V05FReplicate, summarize_v05f


def _qualification():
    return V05AQualification(
        interaction_structural_pass=True,
        interaction_practical_pass=True,
        null_structural_pass=True,
        null_practical_pass=True,
        evidence={},
    )


def _records(identity_error: float = 0.0):
    rows = []
    for replicate in range(16):
        full = -1.90
        knockout = -2.00
        rows.append(
            V05FReplicate(
                world="interaction",
                replicate=replicate,
                truth_beta=0.75,
                posterior_mean=0.75,
                interval_low=0.50,
                interval_high=0.90,
                full_heldout_log_score=full + identity_error,
                partner_knockout_heldout_log_score=knockout,
                heldout_gain=(full + identity_error) - knockout,
                full_divergences=0,
                knockout_divergences=0,
            )
        )
        rows.append(
            V05FReplicate(
                world="measured_shared_null",
                replicate=replicate,
                truth_beta=0.0,
                posterior_mean=0.0,
                interval_low=-0.10,
                interval_high=0.10,
                full_heldout_log_score=-2.01,
                partner_knockout_heldout_log_score=-2.00,
                heldout_gain=-0.01,
                full_divergences=0,
                knockout_divergences=0,
            )
        )
    return rows


def test_v05f_reuses_v05a_thresholds_exactly():
    config = V05AGateConfig()

    assert config.replicates_per_world == 16
    assert config.positive_max_abs_bias == 0.15
    assert config.positive_min_coverage == 0.75
    assert config.positive_min_interval_rate == 0.75
    assert config.positive_min_gain_rate == 0.75
    assert config.positive_min_mean_gain == 0.005
    assert config.null_max_abs_mean == 0.10
    assert config.null_min_coverage == 0.75
    assert config.null_max_nonzero_rate == 0.25
    assert config.null_max_mean_gain == 0.005
    assert config.null_max_material_gain_rate == 0.25
    assert config.max_mean_divergences_per_fit == 0.10


def test_v05f_gate_is_v05a_gate_plus_absolute_score_serialization():
    summary = summarize_v05f(_records())
    decision = evaluate_v05f_gate(_qualification(), summary)

    assert decision.passed
    assert decision.inherited_v05a_decision.passed
    assert len(decision.inherited_v05a_decision.checks) == 18
    assert len(decision.checks) == 19
    assert decision.checks[-1].name == "absolute_score_serialization"
    assert decision.checks[-1].passed


def test_v05f_summary_preserves_original_absolute_scores():
    summary = summarize_v05f(_records())

    assert summary.mean_full_heldout_log_score_by_world["interaction"] == -1.90
    assert summary.mean_knockout_heldout_log_score_by_world["interaction"] == -2.00
    assert summary.inherited_v05a.worlds["interaction"].mean_heldout_gain == pytest.approx(0.10)
    assert summary.inherited_v05a.worlds["measured_shared_null"].mean_heldout_gain == pytest.approx(-0.01)
    assert summary.max_abs_gain_identity_error <= 1e-12


def test_v05f_replicate_rejects_inconsistent_serialized_gain():
    with pytest.raises(ValueError, match="heldout_gain must equal"):
        V05FReplicate(
            world="interaction",
            replicate=0,
            truth_beta=0.75,
            posterior_mean=0.75,
            interval_low=0.50,
            interval_high=0.90,
            full_heldout_log_score=-1.90,
            partner_knockout_heldout_log_score=-2.00,
            heldout_gain=0.09,
            full_divergences=0,
            knockout_divergences=0,
        )
