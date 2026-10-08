from __future__ import annotations
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"docs"/"replication"/"E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json"
REGISTRY=ROOT/"docs"/"replication"/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_frozen_one_shot_artifact_is_pinned_and_nonpromoting():
    r=_read(RESULT)
    p=r["provenance"]
    assert p["workflow_run_id"]==37770893387
    assert p["workflow_run_attempt"]==1
    assert p["artifact_id"]==11547502193
    assert p["artifact_zip_sha256"]=="9a8c6b167c488bdbdd08087a4a5074ca32bbd8c0aa371b181824b2a3cecb01a2"
    assert p["result_json_sha256"]=="2c49577d66d078e5d5fe9200d632ad625baf0fda6f71e8f1cf2792323c2a58ad"
    assert p["published_qualitative_direction_exposed_before_contract"] is True
    assert r["gate_boundary"]["original_standard_E5_qualified"]==0
    assert r["gate_boundary"]["original_standard_E5_G4_passed"] is False
    assert r["gate_boundary"]["original_Findlay_one_shot_rerun"] is False


def test_FOX_observation_stages_oppose_and_product_is_descriptive():
    r=_read(RESULT)
    rows={(x["species"],x["distance_bin"]):x for x in r["stage_cells"]}
    near=rows["FOX","near_le_1m"]
    far=rows["FOX","far_gt_3m"]
    assert near["cctv_reference_passes"]==88
    assert far["cctv_reference_passes"]==175
    assert near["triggered_reference_passes"]==near["registration_eligible_triggered_rows"]==55
    assert far["triggered_reference_passes"]==far["registration_eligible_triggered_rows"]==47
    assert math.isclose(near["p_composite_given_pass"],19/88,abs_tol=1e-12)
    assert math.isclose(far["p_composite_given_pass"],27/175,abs_tol=1e-12)
    assert near["p_trigger"]>far["p_trigger"]
    assert near["p_registration_given_trigger"]<far["p_registration_given_trigger"]
    c=r["near_vs_far"]["FOX"]
    assert c["status"]=="DESCRIPTIVE_OPPOSING_STAGES"
    assert c["log_trigger_ratio"]<0<c["log_registration_ratio"]
    assert math.isclose(c["log_trigger_ratio"]+c["log_registration_ratio"],c["log_composite_ratio"],abs_tol=1e-12)
    assert 0<c["compensation_index"]<1


def test_BADGER_count_mismatch_must_not_create_composite():
    r=_read(RESULT)
    far=next(x for x in r["stage_cells"]
             if x["species"]=="BADGER" and x["distance_bin"]=="far_gt_3m")
    assert far["triggered_reference_passes"]==16
    assert far["registration_eligible_triggered_rows"]==15
    assert far["p_composite_given_pass"] is None
    assert r["near_vs_far"]["BADGER"]["status"]=="COHORT_NONCOMPARABLE"
    assert r["near_vs_far"]["BADGER"]["mismatch_reason_not_proven"] is True


def test_count_agreement_not_passage_identity_and_no_diel_claim():
    r=_read(RESULT)
    q=r["quality_limits"]
    assert q["count_cohort_alignment_does_not_demonstrate_passage_level_record_linkage"] is True
    assert q["FOX_composite_conditioned_on_unverified_row_identity"] is True
    assert q["time_of_day_or_diel_detection_estimated"] is False
    assert q["inferential_confidence_intervals_authorized"] is False
    assert q["geographic_transfer_estimated"] is False


def test_original_E5_registry_unchanged():
    r=_read(REGISTRY)
    assert len(r["candidates"])==17
    assert r["current_conclusion"]["screened_candidate_count"]==17
    assert r["current_conclusion"]["qualified_candidate_count"]==0
    w=next(x for x in r["candidates"]
           if x["candidate_id"]=="wolfson_wildpig_gps_camera_2015_2018")
    assert w["activity_anchor_route"]["empirical_outcome_status"]=="UNRESOLVED"
    assert w["activity_anchor_route"]["quality_status"]=="HOLD_SAMPLE_IDENTITY"
