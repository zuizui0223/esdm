from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V07B_FROZEN_RESULTS.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_v07b_frozen_result_is_single_successful_authorized_run():
    result = _read()

    assert result["status"] == "PASS"
    assert result["outcome_run_id"] == 36074930922
    assert result["outcome_head_sha"] == "87ff01ffb9f10db9b8c2d6ca1bf1d981a7dcb06f"
    assert result["gate_merge_commit"] == "3c7e84203588498c319de8deebd58ae46f244a88"
    assert result["gate_blob_sha"] == result["observed_gate_blob_sha"]
    assert result["result_artifact"]["id"] == 10840405228
    assert result["result_artifact"]["result_json_sha256"] == (
        "c3a5c51b9d8ccbb422b0181ad93d9dc4b1cb405668667e30b4ede0ccb3fef32b"
    )


def test_v07b_recovery_and_transfer_all_pass_frozen_gate():
    result = _read()
    summary = result["summary"]

    assert result["gate"] == {
        "passed": True,
        "checks_passed": 17,
        "checks_total": 17,
    }
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["positive_gain_rate"] == 1.0
    assert summary["mean_gain"] == 7.090827989764034
    assert summary["minimum_gain"] == 3.5637099445650993
    assert summary["total_divergences"] == 0
    assert summary["mean_divergences_per_fit"] == 0.0

    assert all(abs(value) <= 0.25 for value in summary["mean_biases"].values())
    assert all(value >= 0.75 for value in summary["coverages"].values())


def test_v07b_absolute_scores_are_frozen_for_odsp_without_reconstruction():
    result = _read()
    summary = result["summary"]
    schema = result["odsp_ready_result_schema"]

    assert (
        summary["mean_full_heldout_log_score"]
        - summary["mean_occupancy_knockout_heldout_log_score"]
        == summary["mean_gain"]
    )
    assert schema["information_filtration"] == [
        {
            "name": "suitability_only",
            "information": ["suitability"],
            "score_field": "occupancy_knockout_heldout_log_score",
        },
        {
            "name": "suitability_dynamic_occupancy",
            "information": ["suitability", "dynamic_occupancy"],
            "score_field": "full_heldout_log_score",
        },
    ]
    assert schema["score_contract"]["unit"] == "nats_per_heldout_context"


def test_v07b_claim_boundary_stays_marginal_not_movement():
    boundary = _read()["claim_boundary"]

    assert boundary["marginal_dynamic_parameter_recovery"] is True
    assert boundary["late_joint_occurrence_predictive_transfer"] is True
    assert boundary["direct_occupancy_exposure_in_heldout"] is False
    assert boundary["realized_binary_occupancy_history"] is False
    assert boundary["observed_colonization_extinction_events"] is False
    assert boundary["movement_or_dispersal_kernel"] is False
    assert boundary["connectivity_or_resistance"] is False
    assert boundary["causal_movement_limitation"] is False
    assert boundary["odsp_audit_changes_v07b_promotion"] is False
