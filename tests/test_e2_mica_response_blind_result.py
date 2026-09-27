from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = (
    ROOT
    / "docs"
    / "replication"
    / "E2_MICA_RESPONSE_BLIND_GEOMETRY_HEADER_RESULT.json"
)


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_e2_mica_response_blind_result_pins_single_authorized_run():
    result = _read()
    auth = result["authorization"]
    artifact = result["artifact"]

    assert auth["head_sha"] == "42f9988431e72a019777d59a8c4a85205e805049"
    assert auth["implementation_parent_sha"] == (
        "cdf55af51b8b5b4eb453b4660922ce0214e5f961"
    )
    assert auth["workflow_run_id"] == 36316560475
    assert auth["run_attempt"] == 1
    assert auth["conclusion"] == "success"

    assert artifact["id"] == 10930544605
    assert artifact["digest"] == (
        "sha256:48947b418593b0833291c30a9f5394fb911685776c402c6a8b4d0691ae610154"
    )
    assert artifact["result_sha256"] == (
        "b323d03d9c234edf7b9abd1cbb808fae726cc9013a34977d54e4bfeef71f5ae9"
    )


def test_e2_mica_geometry_is_strict_and_well_above_minima():
    result = _read()["result"]

    assert result["status"] == "RESPONSE_BLIND_GEOMETRY_HEADER_PASS"
    assert result["deployment_count"] == 1539
    assert result["training_deployment_count"] == 805
    assert result["heldout_deployment_count"] == 734
    assert result["max_training_longitude"] == 4.841
    assert result["min_heldout_longitude"] == 5.628
    assert result["max_training_longitude"] < result["min_heldout_longitude"]
    assert result["strict_east_extrapolation"] is True
    assert result["longitude_gap"] > 0.78


def test_e2_mica_training_roles_all_pass_by_large_margin():
    counts = _read()["result"]["training_role_counts"]

    assert counts == {
        "opportunistic_presence": 187,
        "calibrated_presence": 197,
        "state_annotated": 266,
        "state_calibration": 155,
    }
    assert min(counts.values()) >= 8


def test_e2_mica_response_boundary_is_still_closed():
    boundary = _read()["response_boundary"]

    assert boundary["observations_data_rows_read"] == 0
    assert boundary["scientific_name_values_read"] is False
    assert boundary["count_values_read"] is False
    assert boundary["state_values_read"] is False
    assert boundary["taxon_frequencies_computed"] is False
    assert boundary["focal_event_counts_computed"] is False
    assert boundary["model_fits"] == 0
    assert boundary["heldout_scores"] == 0
    assert boundary["temporal_opening_completed"] is False
    assert boundary["full_response_opened"] is False


def test_e2_mica_next_stage_is_temporal_only_and_requires_new_authorization():
    next_stage = _read()["next_stage"]

    assert "temporal-integrity-only" in next_stage["allowed"]
    assert next_stage["requires_new_authorization"] is True
    assert (
        next_stage[
            "must_recompute_archive_deployment_split_fingerprints_and_match"
        ]
        is True
    )
    assert next_stage["full_response_remains_forbidden"] is True
