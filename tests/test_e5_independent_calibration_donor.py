from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"docs"/"replication"/"E5_INDEPENDENT_DETECTION_CALIBRATION_DONOR.json"
REGISTRY=ROOT/"docs"/"replication"/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def test_cctv_ground_truth_is_a_component_not_full_e5_qualification():
    e=json.loads(SOURCE.read_text(encoding="utf-8"))
    d=e["original_E5_gate_alignment"]
    assert e["evidence_class"]=="EXTERNAL_G4_COMPONENT_CALIBRATION_WITNESS_NOT_FULL_E5_DATASET"
    assert d["G4_calibration_mechanism"]=="PRESENT_IN_THIS_SOURCE_DESIGN_CCTV_PASS_DENOMINATOR"
    assert d["G3_crossed_geography_source"].startswith("NOT_PASSED")
    assert d["G5_physical_replication"].startswith("NOT_PASSED")
    assert d["G6_temporal_support"].startswith("NOT_PASSED")
    assert d["diel_detection_curve"].startswith("NOT_CONFIRMED")
    assert d["candidate_qualified"] is False
    assert d["not_added_to_17_candidate_registry"] is True
    assert d["biological_focal_response_opening_authorized"] is False


def test_source_files_pinned_and_no_response_rows_inspected():
    e=json.loads(SOURCE.read_text(encoding="utf-8"))
    s=e["source"]
    f=e["response_blind_source_inspection"]
    assert s["public_commit"]=="abc72f535bb59ebed202fb7acca852fc1647e97a"
    assert s["R_analysis_blob_sha"]=="eb8b65cc594737afea3dc5a7a7b831a35d537ec8"
    assert len(s["released_CSV_files"])==5
    assert len({v["blob_sha"] for v in s["released_CSV_files"]})==5
    assert f["released_biological_CSV_data_rows_read"] is False
    assert f["diel_timestamp_column_schema_verified"] is False
    assert f["any_model_fit_authorized"] is False


def test_candidate_count_remains_17_and_rhode_and_wildpig_boundaries_persist():
    v=json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert len(v["candidates"])==17
    assert v["current_conclusion"]["screened_candidate_count"]==17
    assert v["current_conclusion"]["qualified_candidate_count"]==0
    rhode=next(x for x in v["candidates"] if x["candidate_id"]=="rhode_island_paired_cameras_2018_2023")
    wild=next(x for x in v["candidates"] if x["candidate_id"]=="wolfson_wildpig_gps_camera_2015_2018")
    assert "G4" in rhode["gates"]["G4_DETECTION_IDENTIFIABILITY"] or rhode["gates"]["G4_DETECTION_IDENTIFIABILITY"].startswith("FAIL")
    assert wild["activity_anchor_route"]["empirical_outcome_status"]=="UNRESOLVED"
    assert wild["activity_anchor_route"]["quality_status"]=="HOLD_SAMPLE_IDENTITY"
