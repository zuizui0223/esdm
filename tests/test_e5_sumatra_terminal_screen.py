from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / "docs" / "replication" / "E5_SUMATRA_FOCAL_HEADERS_RESULT.json"
RECEIPT = ROOT / "docs" / "replication" / "E5_SUMATRA_FOCAL_HEADERS_RECEIPT.json"
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_SUMATRA_RESPONSE_BLIND_ADJUDICATION.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sumatra_header_resolver_preserves_zero_response_rows():
    value = _read(HEADERS)
    assert value["status"] == "E5_RESPONSE_BLIND_FOCAL_HEADER_RESOLUTION"
    assert [row["header"] for row in value["resolved_headers"]] == [
        "No", "Station_ID", "time", "spc", "sa"
    ]
    assert value["viability_questions"]["station_or_location_identifier_header_present"] is True
    assert value["viability_questions"]["event_timestamp_header_present"] is True
    assert value["viability_questions"]["species_or_taxon_header_present"] is True
    assert value["viability_questions"]["individual_camera_identifier_header_present"] is False
    assert value["viability_questions"]["paired_sensor_or_camera_side_header_present"] is False

    boundary = value["response_boundary"]
    assert boundary["focal_species_data_rows_read"] == 0
    assert boundary["other_species_sheet_rows_read"] == 0
    assert boundary["site_cov_data_rows_read"] == 0
    assert boundary["response_rows_read"] == 0
    assert boundary["focal_response_values_read"] == 0


def test_sumatra_header_receipt_pins_one_shot_artifact():
    value = _read(RECEIPT)
    execution = value["execution"]
    assert execution["workflow_run_id"] == 36788393607
    assert execution["authorization_sha"] == "9ce9de98313b11fd956019e830b1dd9027587776"
    assert execution["artifact_id"] == 11131812567
    assert execution["artifact_digest"] == (
        "sha256:7d4f3bd768b0b2737277e9934c1719240d7fc3e0157a62fe11dc5a419222d761"
    )
    assert execution["result_json_sha256"] == (
        "95d722f8ce7ee2923cdd1a91fbc1b26cd8d639759eb1b37f392dbeb9e683aa85"
    )


def test_sumatra_candidate_stops_on_detection_identifiability_without_response_opening():
    value = _read(SCREEN)
    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert value["hard_stop"]["gate"] == "G4_DETECTION_IDENTIFIABILITY"
    assert value["gates"]["G4_DETECTION_IDENTIFIABILITY"] == (
        "FAIL_PAIRED_SENSOR_IDENTITY_NOT_RETAINED_IN_PUBLIC_RESPONSE_SCHEMA"
    )
    assert value["schema_findings"]["station_identity_retained"] is True
    assert value["schema_findings"]["event_time_retained"] is True
    assert value["schema_findings"]["individual_camera_identity_retained"] is False
    assert value["schema_findings"]["paired_camera_side_or_sensor_identity_retained"] is False
    assert value["response_boundary"]["response_rows_read"] == 0
    assert value["decision"]["focal_response_opening_authorized"] is False
    assert value["decision"]["model_fitting_authorized"] is False
    assert value["decision"]["broader_candidate_search_authorized"] is True


def test_e5_registry_no_longer_marks_stopped_candidates_as_leaders():
    value = _read(REGISTRY)
    by_id = {row["candidate_id"]: row for row in value["candidates"]}

    assert by_id["ecuador_landscape_camera_2023"]["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert by_id["uwin_gallo_10city_2017_2018"]["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert by_id["sumatra_mesopredator_paired_2014_2015"]["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert value["current_conclusion"]["qualified_candidate_selected"] is False
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["strongest_current_named_candidate"] is None
