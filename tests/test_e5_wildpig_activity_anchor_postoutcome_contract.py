from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_WILDPIG_ACTIVITY_ANCHOR_POSTOUTCOME_CONTRACT.json"


def _read() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_postoutcome_contract_is_frozen_before_empirical_completion():
    value = _read()
    assert value["status"] == "FROZEN_BEFORE_EMPIRICAL_OUTCOME_COMPLETION"
    assert value["contract_id"] == "e5-wildpig-activity-anchor-postoutcome-adjudication-v1"
    assert value["decision_mapping"]["SUPPORTED"].endswith("> 0")
    assert "includes 0" in value["decision_mapping"]["UNRESOLVED"]
    assert value["decision_mapping"]["CONTRADICTED"].endswith("< 0")


def test_postoutcome_contract_forbids_selective_rescue():
    value = _read()
    rules = value["postoutcome_rules"]
    assert rules["same_outcome_authorization_may_be_rerun"] is False
    assert rules["model_or_threshold_changes_allowed"] is False
    assert rules["transfer_subset_selection_allowed"] is False
    assert rules["season_subset_selection_allowed"] is False
    assert rules["geography_direction_selection_allowed"] is False
    assert rules["alternate_primary_metric_allowed"] is False


def test_postoutcome_contract_preserves_standard_e5_boundary():
    value = _read()
    reg = value["registry_update_rule"]
    claims = value["claim_boundary"]
    assert reg["standard_E5_G4_must_remain"] == "NOT_PASSED_DIRECT_DETECTION_ROUTE"
    assert reg["standard_candidate_must_remain_unqualified"] is True
    assert reg["original_G4_reclassification_forbidden"] is True
    assert claims["absolute_detection_probability_claim"] is False
    assert claims["abundance_claim"] is False
    assert claims["causal_sensor_mechanism_claim"] is False
    assert claims["original_E5_G4_pass_claim"] is False
    assert claims["untouched_preregistration_claim"] is False
