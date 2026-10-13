from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"replication"
RECEIPT=ROOT/"E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json"
STAGES=ROOT/"E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json"
SENS=ROOT/"E5_FINDLAY_PASSAGE_LINKAGE_SENSITIVITY_RESULT.json"
REG=ROOT/"E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def test_verified_run_provenance_and_881_row_order_evidence():
    x=json.loads(RECEIPT.read_text(encoding="utf-8"))
    p=x["provenance"]
    c=x["frozen_comparison"]
    assert x["status"]=="ROW_ORDER_AGREEMENT_NO_PASS_ID"
    assert p["run_id"]==38351094780
    assert p["run_attempt"]==1
    assert p["artifact_id"]==11790294376
    assert p["artifact_zip_sha256"]=="b052c1a0a46ad65d4fdc9ee7eaffe1c4fc29c8887ab6454ff03c3b535896e3b7"
    assert p["inner_result_json_sha256"]=="27eee40415de794f78c06e30086513ffd42ae7c89cdab6749c2707897ba8b5b1"
    assert c["trigger_csv_rows"]==881==c["registration_csv_rows"]
    assert c["same_row_order_shared_covariate_signatures"]==881
    assert c["same_row_order_trigger_flags"]==881
    assert c["unique_shared_covariate_fingerprint_pairs"]==530
    assert c["identical_but_ambiguous_duplicate_fingerprint_rows"]==351
    assert c["permitted_shared_stable_pass_ID_columns_found"]==0
    assert c["internal_unique_passage_ID_linkage_verified"] is False


def test_forensic_evidence_does_not_relabel_prior_FOX_stages_or_k():
    x=json.loads(RECEIPT.read_text(encoding="utf-8"))
    s=json.loads(STAGES.read_text(encoding="utf-8"))
    a=json.loads(SENS.read_text(encoding="utf-8"))
    d=x["interpretation"]
    assert d["original_FOX_stage_descriptive_claim_promoted_to_confirmatory"] is False
    assert d["actual_mismatch_k_observed_or_bounded"] is False
    assert d["original_BADGER_far_cohort_count_mismatch_unchanged"] is True
    assert d["old_one_shot_repeated"] is False
    assert s["status"]=="RETROSPECTIVE_DESCRIPTIVE_COMPLETED_NO_E5_GATE_PROMOTION"
    assert s["near_vs_far"]["BADGER"]["status"]=="COHORT_NONCOMPARABLE"
    assert a["FOX"]["first_k_to_erase_near_greater_than_far_composite"]==4
    assert a["FOX"]["first_k_to_erase_far_greater_than_near_conditional_registration"]==6
    assert a["observed_k_not_estimated"] is True


def test_e5_original_boundary_not_changed():
    x=json.loads(RECEIPT.read_text(encoding="utf-8"))
    r=json.loads(REG.read_text(encoding="utf-8"))
    assert x["interpretation"]["original_E5_G4_passed"] is False
    assert x["interpretation"]["original_E5_qualified_candidates"]==0
    assert x["data_handling"]["model_fits"]==0
    assert r["current_conclusion"]["screened_candidate_count"]==17
    assert r["current_conclusion"]["qualified_candidate_count"]==0
