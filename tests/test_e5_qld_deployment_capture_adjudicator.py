from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.adjudicate_e5_qld_deployment_capture import adjudicate


def _write(tmp_path: Path, value: dict) -> Path:
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _boundary():
    return {
        "observation_collection_queried": False,
        "media_collection_queried": False,
        "observation_rows_read": 0,
        "media_rows_read": 0,
        "species_fields_read": 0,
        "focal_response_opened": False,
    }


def test_transport_stop_is_terminal_and_does_not_retry(tmp_path):
    path = _write(tmp_path, {
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "status": "E5_DEPLOYMENT_CAPTURE_TRANSPORT_STOP",
        "reason": "missing secret",
        "response_boundary": _boundary(),
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "same_authorization_retry_allowed": False,
        },
    })
    value = adjudicate(
        path,
        artifact_id=1,
        artifact_name="capture",
        artifact_digest="sha256:test",
    )
    assert value["adjudication"]["status"] == (
        "E5_QLD_DEPLOYMENT_CAPTURE_TERMINAL_TRANSPORT_STOP"
    )
    assert value["adjudication"]["geometry_available"] is False
    assert value["adjudication"]["next_same_authorization_retry_allowed"] is False


def test_successful_metadata_capture_is_not_candidate_qualification(tmp_path):
    path = _write(tmp_path, {
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "status": "E5_RESPONSE_BLIND_DEPLOYMENT_METADATA_PRECHECK",
        "response_boundary": _boundary(),
        "deployment_geometry": {
            "row_count": 60,
            "unique_deployment_ids": 60,
            "duplicate_deployment_ids": [],
            "unique_physical_location_candidates": 30,
            "timestamp_parse_failures": 0,
            "nonpositive_interval_rows": 0,
            "distinct_calendar_month_count": 7,
        },
        "protocol_metadata": {
            "camera_model_counts": {"A": 30, "B": 30},
            "feature_type_counts": {"road": 30, "bush": 30},
            "setup_by_counts": {"team": 60},
            "detection_distance_nonempty_rows": 0,
        },
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    })
    value = adjudicate(
        path,
        artifact_id=1,
        artifact_name="capture",
        artifact_digest="sha256:test",
    )
    result = value["adjudication"]
    assert result["status"] == "E5_QLD_DEPLOYMENT_METADATA_CAPTURED"
    assert result["G2_deployment_component_passed"] is True
    assert result["G5_capacity_at_least_30_locations"] is True
    assert result["G6_global_six_month_capacity"] is True
    assert result["candidate_qualified"] is False
    assert value["response_boundary"]["observation_opening_authorized"] is False


def test_response_leak_fails_closed(tmp_path):
    boundary = _boundary()
    boundary["observation_rows_read"] = 1
    path = _write(tmp_path, {
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "status": "E5_DEPLOYMENT_CAPTURE_TRANSPORT_STOP",
        "response_boundary": boundary,
        "decision": {"same_authorization_retry_allowed": False},
    })
    with pytest.raises(ValueError, match="observation rows"):
        adjudicate(
            path,
            artifact_id=1,
            artifact_name="capture",
            artifact_digest="sha256:test",
        )
