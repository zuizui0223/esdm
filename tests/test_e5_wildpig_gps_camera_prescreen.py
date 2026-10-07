from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_wildpig_gps_camera_headers import precheck

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_WILDPIG_GPS_CAMERA_SCREEN.json"
CONTRACT = ROOT / "docs" / "replication" / "E5_WILDPIG_GPS_CAMERA_HEADER_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-wildpig-gps-camera-header-once.yml"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_wildpig_public_file_geometry_crosses_method_and_geography_without_response():
    value = _read(SCREEN)
    gates = {row["gate"]: row["status"] for row in value["gates"]}
    assert value["status"] == "E5_STANDARD_G4_UNPASSED_ACTIVITY_ANCHOR_ROUTE_PENDING_SCHEMA"
    assert value["public_design"]["crossed_method_geography_design"] is True
    assert value["public_design"]["total_camera_sites"] == 92
    assert value["public_design"]["total_gps_individuals"] == 83
    assert gates["G3_CROSSED_DOMAIN"] == "PASS_PUBLIC_FILE_GEOMETRY"
    assert gates["G4_DETECTION_IDENTIFIABILITY"] == (
        "NOT_PASSED_DIRECT_DETECTION_ROUTE"
    )
    assert value["response_boundary"]["data_rows_read"] == 0
    assert value["decision"]["candidate_qualified"] is False


def test_wildpig_header_contract_is_bounded_and_value_blind():
    value = _read(CONTRACT)
    fw = value["response_firewall"]
    assert value["status"] == "FROZEN_HEADER_PRECHECK_NOT_AUTHORIZED"
    assert len(value["source"]["seasonal_files"]) == 16
    assert fw["http_range_max_bytes"] == 1024
    assert fw["first_csv_line_decode_authorized"] is True
    assert fw["second_csv_line_or_later_decode_authorized"] is False
    assert fw["data_rows_read_authorized"] is False
    assert fw["camera_detection_values_authorized"] is False
    assert fw["gps_location_values_authorized"] is False
    assert fw["gps_activity_or_movement_values_authorized"] is False
    assert value["decision_boundary"]["header_precheck_can_qualify_candidate"] is False
    assert value["decision_boundary"]["original_G4_pass_authorized"] is False
    assert value["route_contract"].endswith("E5_EXTERNAL_ACTIVITY_ANCHOR_ROUTE_CONTRACT.json")


def test_wildpig_header_parser_can_validate_both_channels_without_data_rows():
    contract = _read(CONTRACT)

    def fake_fetch(url: str, max_bytes: int) -> bytes:
        if "/GPS/" in url:
            line = "AnimalID,DateTime,Longitude,Latitude\n1,2020-01-01,0,0\n"
        else:
            line = "CameraID,DateTime,Species\nA,2020-01-01,Sus scrofa\n"
        return line.encode("utf-8")[:max_bytes]

    result = precheck(contract, fetcher=fake_fetch)
    summary = result["schema_summary"]
    boundary = result["response_boundary"]
    assert summary["camera_files_checked"] == 8
    assert summary["gps_files_checked"] == 8
    assert summary["camera_schema_viable_all_files"] is True
    assert summary["gps_external_activity_schema_viable_all_files"] is True
    assert summary["crossed_method_geography_file_geometry_preserved"] is True
    assert boundary["data_rows_decoded"] == 0
    assert boundary["camera_detection_values_read"] == 0
    assert boundary["gps_location_or_activity_values_read"] == 0
    assert result["decision"]["candidate_qualified"] is False
    assert result["decision"]["value_blind_child_contract_recommended"] is True


def test_wildpig_workflow_pins_contract_and_has_no_manual_dispatch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/wildpig-gps-camera-header-v1" in text
    assert "E5_WILDPIG_GPS_CAMERA_HEADER_AUTHORIZED.json" in text
    assert "3d9de43f30e89e2af9dae803f97ebf1f4cb82593" in text
    assert "workflow_dispatch" not in text
    assert "data_rows_authorized" in text


def test_registry_names_wildpig_as_strongest_unqualified_candidate():
    value = _read(REGISTRY)
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "wolfson_wildpig_gps_camera_2015_2018"
    )
    assert value["current_conclusion"]["screened_candidate_count"] == 16
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["strongest_current_named_candidate"] == (
        "wolfson_wildpig_gps_camera_2015_2018"
    )
    assert row["response_opened"] is False
    assert row["response_may_be_opened_for_E5"] is False
    assert row["decision"] == "E5_STANDARD_CANDIDATE_NOT_QUALIFIED_ACTIVITY_ANCHOR_ROUTE_HEADER_PENDING"
