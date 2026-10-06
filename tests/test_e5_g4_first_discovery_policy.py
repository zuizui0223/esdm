import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"docs"/"replication"/"E5_G4_FIRST_DISCOVERY_POLICY.json"

def test_g4_first_policy_preserves_frozen_e5_gates_and_response_firewall():
    v=json.loads(PATH.read_text(encoding="utf-8"))
    assert v["status"]=="FROZEN_RESPONSE_BLIND_DISCOVERY_POLICY"
    assert v["rationale"]["screened_candidates"]==14
    assert v["rationale"]["qualified_candidates"]==0
    assert v["rationale"]["dominant_bottleneck"]=="joint_G3_G4_identifiability"
    assert v["decision"]["frozen_E5_gates_changed"] is False
    assert v["decision"]["candidate_selected"] is False
    assert v["decision"]["response_opening_authorized"] is False
    assert v["decision"]["model_fitting_authorized"] is False
    assert v["response_boundary"]["focal_response_opened"] is False
    assert v["response_boundary"]["response_values_allowed_for_discovery"] is False

def test_g4_first_policy_rejects_collapsed_pair_identity_and_camera_model_only_designs():
    v=json.loads(PATH.read_text(encoding="utf-8"))
    d1=v["hard_entry_requirements"][0]
    text=" ".join(d1["reject_if"])
    assert "collapses pair-member identity" in text
    assert "camera model names exist" in text
    assert v["hard_entry_requirements"][1]["id"]=="D2_GEOGRAPHIC_OVERLAP"
