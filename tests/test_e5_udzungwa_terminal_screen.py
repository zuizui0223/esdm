from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"docs"/"replication"/"E5_UDZUNGWA_HEADER_RESULT.json"
RECEIPT=ROOT/"docs"/"replication"/"E5_UDZUNGWA_HEADER_RECEIPT.json"
SCREEN=ROOT/"docs"/"replication"/"E5_CANDIDATE_UDZUNGWA_SCREEN.json"
REGISTRY=ROOT/"docs"/"replication"/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"

def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_udzungwa_formal_header_run_read_no_data_rows():
    r=_read(RESULT)
    assert r["status"]=="E5_RESPONSE_BLIND_HEADER_PRECHECK"
    assert r["response_boundary"]["header_lines_read"]==1
    assert r["response_boundary"]["data_rows_read"]==0
    assert r["response_boundary"]["response_rows_read"]==0
    assert r["source"]["observed_md5"]=="fb6c9a82c237b8ec3ef80aa8933b8ede"

def test_udzungwa_public_schema_loses_paired_sensor_identity():
    r=_read(RESULT)
    v=r["schema_viability"]
    assert v["station_or_location"] is True
    assert v["deployment_start"] is True
    assert v["deployment_end"] is True
    assert v["event_timestamp"] is True
    assert v["individual_camera"] is False
    assert v["paired_sensor_or_camera_side"] is False

def test_udzungwa_terminal_screen_fails_g4_without_opening_response():
    s=_read(SCREEN)
    gates={x["gate"]:x for x in s["gates"]}
    assert s["status"]=="E5_CANDIDATE_NOT_QUALIFIED"
    assert gates["G4_DETECTION_IDENTIFIABILITY"]["status"]==(
        "FAIL_PAIRED_SENSOR_IDENTITY_NOT_RETAINED_IN_PUBLIC_RESPONSE_SCHEMA"
    )
    assert s["decision"]["hard_stop_gate"]=="G4_DETECTION_IDENTIFIABILITY"
    assert s["decision"]["focal_response_opening_authorized"] is False
    assert s["decision"]["model_fitting_authorized"] is False

def test_udzungwa_receipt_pins_one_shot_artifact():
    r=_read(RECEIPT)
    e=r["execution"]
    assert e["workflow_run_id"]==37254391448
    assert e["authorization_sha"]=="c7861e0a9d345f57cdc05c76324d921fe0a0663b"
    assert e["artifact_id"]==11321554847
    assert e["artifact_digest"]==(
        "sha256:9b9923e01d9dd9d35490661301e5613e391ebfe087610abe5be2e9e7c64f6e20"
    )
    assert e["result_json_sha256"]==(
        "7b88b20163612343bfa4d9a06c40ae40341236c7829a99e7ec796c04cbb6510d"
    )

def test_registry_has_fifteen_candidates_and_kays41_is_strongest_unresolved():
    v=_read(REGISTRY)
    assert v["current_conclusion"]["screened_candidate_count"]==15
    assert v["current_conclusion"]["qualified_candidate_count"]==0
    assert v["current_conclusion"]["strongest_current_named_candidate"]==(
        "kays41_emammal_team_2020"
    )
    row=next(x for x in v["candidates"] if x["candidate_id"]=="udzungwa_paired_arrays_2013_2014")
    assert row["decision"]=="E5_CANDIDATE_NOT_QUALIFIED"
    assert row["response_may_be_opened_for_E5"] is False
