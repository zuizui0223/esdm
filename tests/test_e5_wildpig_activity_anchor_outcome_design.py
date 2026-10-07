from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTCOME=ROOT/"docs"/"replication"/"E5_WILDPIG_ACTIVITY_ANCHOR_OUTCOME_CONTRACT.json"
MODEL=ROOT/"docs"/"replication"/"E5_WILDPIG_ACTIVITY_ANCHOR_MODEL_CONTRACT.json"
WORKFLOW=ROOT/".github"/"workflows"/"e5-wildpig-activity-anchor-outcome-once.yml"
RUNNER=ROOT/"scripts"/"run_e5_wildpig_activity_anchor_transfer.R"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_outcome_contract_keeps_empirical_rows_closed_until_marker():
    v=_read(OUTCOME)
    assert v["status"]=="FROZEN_OUTCOME_NOT_AUTHORIZED"
    assert v["parent_model_blob_sha"]=="910ffca4af2be05cf7d034586cb5e29a8ec0d446"
    assert v["response_firewall"]["empirical_opening_authorized_now"] is False
    assert v["response_firewall"]["focal_camera_event_values_authorized_now"] is False
    assert v["response_firewall"]["gps_location_values_authorized_now"] is False
    assert v["response_firewall"]["model_fitting_authorized_now"] is False
    assert v["claim_boundary"]["result_is_standard_E5_G4_validation"] is False
    assert v["claim_boundary"]["untouched_preregistration_claim"] is False


def test_outcome_workflow_is_marker_only_and_pins_both_contracts():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert "e5/wildpig-activity-anchor-outcome-v1" in text
    assert "E5_WILDPIG_ACTIVITY_ANCHOR_OUTCOME_AUTHORIZED.json" in text
    assert "fdfed4e3e5bd9ee0d96a3caeca1fe286b56148dc" in text
    assert "910ffca4af2be05cf7d034586cb5e29a8ec0d446" in text
    assert "workflow_dispatch" not in text
    assert "expected exactly 16 frozen input files" in text
    assert "rm -rf build/private" in text


def test_runner_contains_frozen_symmetric_transfer_and_claim_limits():
    text=RUNNER.read_text(encoding="utf-8")
    assert 'geographies <- c("FL", "CA")' in text
    assert 'seasons <- c("spring", "summer", "fall", "winter")' in text
    assert "for (train in geographies)" in text
    assert "corrected-baseline" in text
    assert "for (b in 1:1000)" in text
    assert 'original_G4_passed=FALSE' in text
    assert 'absolute_detection_probability_identified=FALSE' in text


def test_model_contract_and_outcome_contract_share_route_boundary():
    m=_read(MODEL)
    o=_read(OUTCOME)
    assert m["route_id"]==o["route_id"]=="e5-external-activity-anchor-v1"
    assert m["claims_if_executed"]["may_claim_original_E5_G4_pass"] is False
    assert o["claim_boundary"]["absolute_detection_probability_claim"] is False
