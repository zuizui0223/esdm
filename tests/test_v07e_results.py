import json
from pathlib import Path


def _payload():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07E_FROZEN_RESULTS.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_v07e_frozen_result_is_exact_authorized_pass():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["outcome_run_id"] == 36088717290
    assert payload["outcome_head_sha"] == (
        "0ca249e3acaadc69eace3166970f4bf6619924ab"
    )
    assert payload["gate_freeze_commit"] == (
        "a047fdb0fd7843b83169d5b168d86de005143c3b"
    )
    assert payload["gate_blob_sha"] == (
        "e089e43ff009d11e87a16cd7f1c18276b0017f41"
    )
    assert payload["observed_gate_blob_sha"] == payload["gate_blob_sha"]


def test_v07e_artifact_digests_are_independently_matched():
    payload = _payload()

    qualification = payload["qualification_artifact"]
    result = payload["result_artifact"]

    assert qualification["id"] == 10844318765
    assert qualification["github_digest"] == (
        "sha256:" + qualification["independent_zip_sha256"]
    )
    assert result["id"] == 10844319589
    assert result["github_digest"] == (
        "sha256:" + result["independent_zip_sha256"]
    )


def test_v07e_reciprocal_gate_passed_with_zero_divergences():
    payload = _payload()
    summary = payload["summary"]

    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 9
    assert payload["gate"]["checks_total"] == 9
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["static_better_rate"] == 1.0
    assert summary["mean_static_gain"] >= 0.50
    assert summary["minimum_static_gain"] > 0.0
    assert summary["total_divergences"] == 0


def test_v07e_claim_boundary_stays_bounded():
    boundary = _payload()["interpretation_boundary"]

    assert boundary["reciprocal_model_resolution_specificity_established"] is True
    assert boundary["dynamic_world_dynamic_advantage_from_v07d"] is True
    assert boundary["static_world_static_advantage_from_v07e"] is True
    assert boundary["equal_parameter_count"] is True
    assert boundary["matched_observation_programme"] is True
    assert boundary["heldout_direct_occupancy_exposure"] is False

    assert boundary["universal_model_selection_consistency_established"] is False
    assert boundary["realized_binary_occupancy_history_established"] is False
    assert boundary["colonization_extinction_events_observed"] is False
    assert boundary["movement_kernel_identified"] is False
    assert boundary["connectivity_identified"] is False
    assert boundary["source_sink_dynamics_identified"] is False
    assert boundary["empirical_biological_validity"] is False
