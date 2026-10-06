from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_kays41_raw_header import (
    _match_concepts,
    _parse_header,
    _transport_stop,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_KAYS41_RAW_HEADER_CONTRACT.json"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_is_header_only_and_requires_partial_content():
    value = _contract()
    assert value["status"] == "FROZEN_HEADER_PRECHECK_NOT_AUTHORIZED"
    assert value["transport_contract"]["accepted_http_status"] == [206]
    assert value["transport_contract"]["full_file_download_authorized"] is False
    assert value["transport_contract"]["retry_authorized"] is False
    firewall = value["response_firewall"]
    assert firewall["header_line_read_authorized"] is True
    assert firewall["data_row_read_authorized"] is False
    assert firewall["response_value_read_authorized"] is False
    assert firewall["species_value_read_authorized"] is False
    assert firewall["model_fitting_authorized"] is False


def test_schema_parser_can_find_candidate_specific_calibration_fields():
    raw = (
        b"DeploymentID,Site_ID,Study_Area,Camera_ID,Camera_Model,"
        b"Deployment_Start,Deployment_End,Photo_Date,Photo_Time,"
        b"Scientific_Name,Trigger_Detection_Distance_m\n"
    )
    header, digest = _parse_header(raw, 8192)
    assert len(digest) == 64
    concepts = _match_concepts(header)
    assert concepts["deployment_identifier"] == ["DeploymentID"]
    assert concepts["physical_location_identifier"] == ["Site_ID"]
    assert concepts["study_or_project_identifier"] == ["Study_Area"]
    assert concepts["camera_or_device_identifier"] == ["Camera_ID"]
    assert concepts["camera_model_or_make"] == ["Camera_Model"]
    assert concepts["deployment_start"] == ["Deployment_Start"]
    assert concepts["deployment_end"] == ["Deployment_End"]
    assert concepts["event_time"] == ["Photo_Time"]
    assert concepts["taxon_identity_field"] == ["Scientific_Name"]
    assert concepts["detection_distance_or_calibration"] == [
        "Trigger_Detection_Distance_m"
    ]


def test_incomplete_header_fails_closed():
    try:
        _parse_header(b"DeploymentID,Site_ID", 8192)
    except ValueError as exc:
        assert "newline-terminated" in str(exc)
    else:
        raise AssertionError("incomplete range must fail closed")


def test_transport_stop_never_promotes_or_opens_response():
    value = _transport_stop(_contract(), "HTTP transport failed", 403)
    boundary = value["response_boundary"]
    assert value["status"] == "E5_RESPONSE_BLIND_RAW_HEADER_TRANSPORT_STOP"
    assert boundary["header_lines_read"] == 0
    assert boundary["data_rows_read"] == 0
    assert boundary["response_values_read"] == 0
    assert boundary["species_values_read"] == 0
    assert boundary["focal_response_opened"] is False
    assert value["decision"]["candidate_qualified"] is False
    assert value["decision"]["same_authorization_rerun_allowed"] is False
