from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"replication"
RECEIPT=ROOT/"E5_RHODE_ISLAND_DEPLOYMENT_GEOMETRY_RECEIPT.json"
REGISTRY=ROOT/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"
PROOF=ROOT/"E5_RHODE_ISLAND_PAIRED_PRODUCT_NONIDENTIFICATION.json"


def test_one_shot_receipt_evidence_and_response_firewall():
    v=json.loads(RECEIPT.read_text(encoding="utf-8"))
    p=v["provenance"]
    assert p["workflow_run_id"]==37765754779
    assert p["workflow_job_id"]==113272885181
    assert p["artifact_id"]==11544492725
    assert p["artifact_zip_sha256"]=="cafcec32ef9636cf026bca7b39e365cf711234fed0ae5887c8909d9644afaa2c"
    assert p["result_json_sha256"]=="a0a67b7ed1adae0f5f7275570c75594abed531e25786997fd29fe9355a7497d4"
    assert v["response_firewall"]["deployment_metadata_rows_processed"]==2982
    assert v["response_firewall"]["detection_csv_member_opened"] is False
    assert v["response_firewall"]["biological_response_rows_processed"]==0
    assert v["response_firewall"]["model_fitting"] is False


def test_geo_pair_exposure_passes_numerical_geometry_but_not_g4():
    v=json.loads(RECEIPT.read_text(encoding="utf-8"))
    d=v["deployment"]
    assert d["rows"]==2982
    assert d["valid_effort_rows"]==2982
    assert d["valid_site_period_groups"]==1488
    assert d["site_identifiers_with_consistent_coordinates"]==264
    assert d["site_identifiers_with_spatial_conflict"]==1
    assert d["published_site_count"]==249
    assert d["published_site_count_mismatch_resolved"] is False
    west=v["operational_blocks"]["WEST_OPERATIONAL"]
    east=v["operational_blocks"]["EAST_OPERATIONAL"]
    assert west["independent_site_IDs_with_valid_effort"]==132
    assert east["independent_site_IDs_with_valid_effort"]==132
    assert west["site_IDs_with_matched_camera_operational_overlap"]==126
    assert east["site_IDs_with_matched_camera_operational_overlap"]==120
    assert west["site_period_groups_with_overlap"]==692
    assert east["site_period_groups_with_overlap"]==630
    assert len(west["calendar_month_numbers"])==12
    assert len(east["calendar_month_numbers"])==12
    assert v["fixed_interpretation"]["G4"].startswith("NOT_PASSED")
    assert v["fixed_interpretation"]["full_candidate_qualified"] is False


def test_registry_terminal_original_e5_and_no_separate_detection_claim():
    v=json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert v["current_conclusion"]["screened_candidate_count"]==17
    assert v["current_conclusion"]["qualified_candidate_count"]==0
    assert v["current_conclusion"]["strongest_current_named_candidate"]=="kays41_emammal_team_2020"
    r=next(c for c in v["candidates"] if c["candidate_id"]=="rhode_island_paired_cameras_2018_2023")
    assert r["decision"]=="E5_CANDIDATE_NOT_QUALIFIED_AT_G4_CURRENT_PUBLIC_PAIR_DESIGN"
    assert r["response_opened"] is False
    assert r["response_may_be_opened_for_E5"] is False
    assert r["gates"]["G4_DETECTION_IDENTIFIABILITY"]=="FAIL_CURRENT_UNCALIBRATED_PAIR_PRODUCT_GAUGE"
    assert r["public_metadata"]["spatially_conflicting_site_IDs"]==1
    assert r["public_metadata"]["detection_CSV_member_opened"] is False


def test_synthetic_nonidentification_witness_prevents_promotion():
    p=json.loads(PROOF.read_text(encoding="utf-8"))
    assert p["status"]=="FROZEN_RESPONSE_FREE_NECESSARY_G4_OBLIGATION"
    assert p["outcome_firewall"]["source_CSV_data_rows_opened"] is False
    assert p["candidate_decision"].startswith("G4 REMAINS UNPASSED")
