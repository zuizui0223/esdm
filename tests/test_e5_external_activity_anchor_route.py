from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / "docs" / "replication" / "E5_EXTERNAL_ACTIVITY_ANCHOR_ROUTE_CONTRACT.json"


def test_activity_anchor_route_does_not_reclassify_original_g4():
    value = json.loads(ROUTE.read_text(encoding="utf-8"))
    rel = value["relationship_to_existing_e5"]
    assert value["status"] == "FROZEN_PRE_RESPONSE_ALTERNATIVE_ROUTE"
    assert rel["original_G4_changed"] is False
    assert rel["original_candidate_qualification_contract_changed"] is False
    assert rel["prior_candidate_outcomes_reclassified"] is False
    assert rel["wildpig_original_G4_passed"] is False
    assert value["claims_if_route_eventually_qualifies"]["original_E5_G4_pass_claim"] is False


def test_activity_anchor_route_identifies_only_relative_diel_distortion():
    value = json.loads(ROUTE.read_text(encoding="utf-8"))
    target = value["identification_target"]
    assert "A_gs(t)" in target["activity_curve"]
    assert "D_gs(t)" in target["camera_observation_distortion"]
    assert target["absolute_detection_probability_identified"] is False
    assert target["abundance_identified"] is False
    assert target["sensor_detection_probability_identified"] is False
    assert "multiplicative constant" in target["identification_scale"]


def test_activity_anchor_route_keeps_response_closed_until_route_gates_pass():
    value = json.loads(ROUTE.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["focal_camera_event_values_opened"] is False
    assert fw["gps_location_values_opened"] is False
    assert fw["gps_movement_values_opened"] is False
    assert fw["effect_direction_opened"] is False
    assert fw["camera_vs_gps_overlap_values_opened"] is False
    assert fw["predictive_scores_opened"] is False
    assert fw["model_fitting_authorized"] is False


def test_activity_anchor_route_requires_crossed_geographies_and_model_freeze():
    value = json.loads(ROUTE.read_text(encoding="utf-8"))
    crossed = value["crossed_design_requirements"]
    frozen = value["model_freeze_requirements_before_values"]
    assert crossed["minimum_geographic_regimes"] == 2
    assert crossed["both_camera_and_activity_anchor_required_in_each_geography"] is True
    assert crossed["overlapping_seasonal_support_required"] is True
    assert frozen["D_normalization_constraint_must_be_frozen"] is True
    assert frozen["heldout_geography_rule_must_be_frozen"] is True
    assert frozen["post_response_model_selection_allowed"] is False
