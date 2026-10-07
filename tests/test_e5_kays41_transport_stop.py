from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STOP = (
    ROOT / "docs" / "replication"
    / "E5_KAYS41_DICTIONARY_TRANSPORT_STOP.json"
)
REGISTRY = (
    ROOT / "docs" / "replication"
    / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_kays41_dictionary_stop_is_transport_only_and_response_blind():
    value = _read(STOP)
    b = value["response_boundary"]

    assert value["status"] == "TERMINAL_TRANSPORT_STOP_NO_DICTIONARY_READ"
    assert b["dictionary_files_read"] == 0
    assert b["response_files_downloaded"] == 0
    assert b["response_files_opened"] == 0
    assert b["detection_rows_read"] == 0
    assert b["species_values_read"] == 0
    assert b["focal_response_opened"] is False


def test_kays41_transport_receipt_pins_one_authorized_run():
    value = _read(STOP)
    execution = value["execution"]

    assert execution["workflow_run_id"] == 37212411945
    assert execution["authorization_sha"] == (
        "661dc0c96dd618cb23a6b231a5131194959aa3a3"
    )
    assert execution["artifact_id"] == 11307385563
    assert execution["artifact_digest"] == (
        "sha256:488fa9a9ab5f5265f79a4bb7a25da624307fc86c7b6c8d6e5635c80758a57bba"
    )
    assert execution["result_json_sha256"] == (
        "a98fd3e7cbbf707ae921d0d5167edc9bc6a67ece072c645cadb1034409abe231"
    )
    assert value["governance"]["same_authorization_rerun_allowed"] is False
    assert value["governance"]["candidate_scientific_status_changed"] is False


def test_registry_keeps_kays41_unqualified_after_transport_stop():
    value = _read(REGISTRY)
    row = next(
        item for item in value["candidates"]
        if item["candidate_id"] == "wolfson_wildpig_gps_camera_2015_2018"
    )

    assert row["decision"] == "E5_CANDIDATE_NOT_YET_QUALIFIED_TRANSPORT_BLOCKED"
    assert row["response_opened"] is False
    assert row["public_metadata"]["dictionary_rows_read"] == 0
    assert row["public_metadata"]["response_files_downloaded"] == 0
    assert row["response_may_be_opened_for_E5"] is False

    current = value["current_conclusion"]
    assert current["screened_candidate_count"] == 16
    assert current["qualified_candidate_count"] == 0
    assert current["strongest_current_named_candidate"] == "wolfson_wildpig_gps_camera_2015_2018"
    assert current["response_opening_authorized"] is False
    assert current["model_fitting_authorized"] is False
