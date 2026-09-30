from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT / "docs" / "replication"
    / "E5_INDEPENDENT_ACTIVITY_DETECTION_QUALIFICATION_CONTRACT.json"
)


def _read() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e5_qualification_is_frozen_before_candidate_search_and_response():
    value = _read()

    assert value["status"] == "FROZEN_PRE_CANDIDATE_SEARCH"
    boundary = value["outcome_boundary"]
    assert boundary["candidate_search_authorized"] is True
    assert boundary["metadata_schema_geometry_opening_authorized"] is True
    assert boundary["focal_response_opening_authorized"] is False
    assert boundary["model_fitting_authorized"] is False
    assert boundary["E5_outcome_contract_exists"] is False
    assert boundary["requires_separate_selected_candidate_contract"] is True
    assert boundary["requires_separate_response_opening_authorization"] is True


def test_e5_requires_independent_response_and_forbids_mica_snapshot_reuse():
    value = _read()
    firewall = value["independence_firewall"]
    independent = value["candidate_qualification"]["independence"]

    assert firewall["primary_test_may_use_E2_E4_MICA_response"] is False
    assert firewall["primary_test_may_use_Snapshot_Japan_response"] is False
    assert firewall["candidate_must_be_new_independent_response_dataset"] is True
    assert independent["new_response_dataset_required"] is True
    assert independent["not_MICA_v3_or_derivative"] is True
    assert independent["not_Snapshot_Japan_2023_or_derivative"] is True


def test_e5_requires_geography_source_crossing_and_detection_identification():
    value = _read()["candidate_qualification"]
    crossed = value["crossed_domain_design"]
    detection = value["effective_detection_information"]

    assert crossed["perfect_geography_source_confounding_is_hard_stop"] is True
    assert len(crossed["acceptable_designs"]) >= 3
    assert detection["required"] is True
    assert detection["fixed_detection_equal_one_without_external_calibration_is_sufficient"] is False
    assert detection["camera_make_or_metadata_alone_without_identifying_variation_is_sufficient"] is False
    assert detection["activity_detection_intercept_only_confounding_is_hard_stop"] is True
    assert len(detection["acceptable_paths"]) >= 3


def test_e5_freezes_physical_clusters_and_diel_nonstationarity_terms():
    value = _read()["candidate_qualification"]
    physical = value["physical_replication"]
    activity = value["predeclared_activity_structure"]

    assert physical["physical_location_identifier_required"] is True
    assert physical["repeated_deployments_at_same_location_must_be_nested_under_location"] is True
    assert physical["minimum_independent_physical_locations_training"] == 20
    assert physical["minimum_independent_physical_locations_heldout"] == 10
    assert physical["heldout_location_overlap_with_training_for_primary_geographic_transfer"] == 0
    assert "geographic_or_source_domain_by_diel" in activity["required_nonstationarity_terms"]
    assert "season_by_diel" in activity["required_nonstationarity_terms"]
    assert activity["post_response_interaction_selection_allowed"] is False


def test_e5_all_pre_response_gates_are_required_and_do_not_open_outcome():
    value = _read()

    names = [row["gate"] for row in value["pre_response_gates"]]
    assert names == [
        "G1_INDEPENDENT_SOURCE",
        "G2_SCHEMA_EFFORT_TIME",
        "G3_CROSSED_DOMAIN",
        "G4_DETECTION_IDENTIFIABILITY",
        "G5_PHYSICAL_REPLICATION",
        "G6_TEMPORAL_SUPPORT",
        "G7_MODEL_FREEZE",
    ]
    decision = value["candidate_decision"]
    assert decision["all_pre_response_gates_required"] is True
    assert decision["failure_is_not_scientific_negative_result"] is True
    assert decision["failing_candidate_may_not_be_repaired_using_its_focal_response"] is True

    governance = value["claims_if_eventually_qualified"]
    assert governance["causal_behavior_claim"] is False
    assert governance["universal_camera_detection_claim"] is False
    assert governance["universal_taxon_claim"] is False
    assert governance["E4_confirmation_claim"] is False
