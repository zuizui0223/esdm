import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V07B_FROZEN_RESULTS.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_v07b_frozen_result_records_exact_pass_provenance():
    result = _read()

    assert result["status"] == "PASS"
    assert result["outcome_run_id"] == 36076155807
    assert result["outcome_head_sha"] == (
        "c1622dea9168d1f8ad9a57ed5ecf823fa0953f49"
    )
    assert result["gate_freeze_commit"] == (
        "e1f805c6681d33bfc92758b2cdf9d95673353ccc"
    )
    assert result["gate_blob_sha"] == (
        "b0f721ac334a2e76e0387510f5a889980eaefe53"
    )
    assert result["result_artifact"]["id"] == 10839488324
    assert result["result_artifact"]["independent_zip_sha256"] == (
        "ac2f9d51fef951a188de037dcf04c6444531a741d8309cb7ae45383d2428784e"
    )


def test_v07b_frozen_result_preserves_identification_boundary():
    result = _read()
    q = result["qualification"]

    assert q["joint_only_rank"] == 3
    assert q["joint_only_parameter_count"] == 4
    assert q["joint_only_all_targets_not_identified"] is True
    assert q["direct_rank"] == 4
    assert q["direct_all_targets_identified"] is True
    assert max(q["target_sd_proxies"].values()) <= 0.25


def test_v07b_frozen_result_passes_recovery_and_late_transfer():
    result = _read()
    summary = result["summary"]

    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert max(abs(value) for value in summary["mean_biases"].values()) <= 0.20
    assert min(summary["coverages"].values()) >= 0.75
    assert summary["positive_late_transfer_rate"] == 1.0
    assert summary["mean_late_transfer_gain"] >= 0.50
    assert summary["minimum_late_transfer_gain"] > 0.0
    assert summary["total_divergences"] == 0
    assert result["gate"] == {
        "passed": True,
        "checks_passed": 16,
        "checks_total": 16,
    }


def test_v07b_result_does_not_overclaim_dynamic_mechanism():
    boundary = _read()["interpretation_boundary"]

    assert boundary["marginal_dynamic_parameter_recovery_established"] is True
    assert boundary["late_joint_occurrence_transfer_established"] is True
    assert boundary["heldout_direct_occupancy_exposure"] is False
    assert boundary["dynamic_superiority_over_matched_static_occupancy_established"] is False
    assert boundary["realized_binary_occupancy_history_established"] is False
    assert boundary["colonization_extinction_events_observed"] is False
    assert boundary["movement_kernel_identified"] is False
    assert boundary["connectivity_identified"] is False
