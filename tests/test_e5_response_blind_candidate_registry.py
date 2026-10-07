from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e5_candidate_registry_keeps_response_closed():
    value = _read()
    firewall = value["selection_firewall"]
    assert value["status"] == "RESPONSE_BLIND_SEARCH_IN_PROGRESS"
    assert firewall["focal_response_opened"] is False
    assert firewall["focal_event_counts_used_for_selection"] is False
    assert firewall["focal_diel_direction_used_for_selection"] is False
    assert firewall["predictive_scores_used_for_selection"] is False
    assert value["current_conclusion"]["response_opening_authorized"] is False
    assert value["current_conclusion"]["model_fitting_authorized"] is False


def test_snapshot_usa_2024_fails_frozen_temporal_gate_before_response():
    value = _read()
    row = next(x for x in value["candidates"] if x["candidate_id"] == "snapshot_usa_2024")
    assert row["public_metadata"]["deployment_records"] == 3127
    assert row["public_metadata"]["camera_trap_arrays"] == 184
    assert row["public_metadata"]["states"] == 49
    assert row["public_metadata"]["distance_calibration_arrays"] == 73
    assert row["gates"]["G6_TEMPORAL_SUPPORT"] == "FAIL"
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert row["response_may_be_opened_for_E5"] is False


def test_double_observer_candidate_fails_replication_and_temporal_gates():
    value = _read()
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "nakashima_double_observer_2022"
    )
    assert row["public_metadata"]["japan_camera_stations"] == 7
    assert row["public_metadata"]["cameroon_camera_stations"] == 26
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"] == "PASS_DESIGN_PRINCIPLE"
    assert row["gates"]["G5_PHYSICAL_REPLICATION"] == "FAIL"
    assert row["gates"]["G6_TEMPORAL_SUPPORT"] == "FAIL"
    assert row["response_may_be_opened_for_E5"] is False


def test_wildlife_insights_is_discovery_pool_not_selected_outcome():
    value = _read()
    universe = value["search_universes"][0]
    assert universe["universe_id"] == "wildlife_insights_public_projects"
    assert universe["role"] == "PRIMARY_RESPONSE_BLIND_DISCOVERY_POOL"
    assert value["current_conclusion"]["qualified_candidate_selected"] is False
    assert value["current_conclusion"]["strongest_current_discovery_pool"] == (
        "Wildlife Insights public projects and independently published paired/calibrated camera-trap packages"
    )


def test_yearlong_uljin_candidate_still_fails_crossed_domain_gate():
    value = _read()
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "uljin_korea_2022_2023"
    )
    assert row["public_metadata"]["physical_camera_stations"] == 82
    assert row["gates"]["G5_PHYSICAL_REPLICATION"] == "PASS_COUNTS"
    assert row["gates"]["G6_TEMPORAL_SUPPORT"] == "PASS"
    assert row["gates"]["G3_CROSSED_DOMAIN"] == "FAIL"
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert row["response_may_be_opened_for_E5"] is False


def test_longterm_amazon_candidate_is_not_rescued_by_duration_or_paired_subset():
    value = _read()
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "eastern_amazon_jaguar_2014_2020"
    )
    assert row["public_metadata"]["physical_camera_locations"] == 42
    assert row["public_metadata"]["paired_camera_locations"] == 11
    assert row["gates"]["G5_PHYSICAL_REPLICATION"] == "PASS_COUNTS"
    assert row["gates"]["G6_TEMPORAL_SUPPORT"] == "PASS"
    assert row["gates"]["G2_SCHEMA_EFFORT_TIME"].startswith("FAIL")
    assert row["gates"]["G3_CROSSED_DOMAIN"] == "FAIL"
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"


def test_registry_has_no_qualified_candidate_after_sixteen_response_blind_screens():
    value = _read()
    assert value["current_conclusion"]["screened_candidate_count"] == 16
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert not any(
        row.get("decision") == "E5_CANDIDATE_QUALIFIED_PRE_RESPONSE"
        for row in value["candidates"]
    )


def test_sunda_candidate_is_promising_but_blocked_before_response_opening():
    value = _read()
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "sunda_islands_multistudy_2007_2016"
    )
    assert row["public_metadata"]["sampling_locations"] == 22
    assert row["public_metadata"]["camera_trap_stations"] == 1544
    assert row["public_metadata"]["trap_nights"] == 138515
    assert row["public_metadata"]["cameras_per_station"] == 2
    assert row["gates"]["G2_SCHEMA_EFFORT_TIME"] == (
        "BLOCKED_RAW_EVENT_ACCESS_NOT_ESTABLISHED"
    )
    assert row["gates"]["G3_CROSSED_DOMAIN"].startswith("PROMISING")
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"] == "PENDING_EVENT_OCCASION_STRUCTURE"
    assert row["decision"] == "E5_CANDIDATE_NOT_YET_QUALIFIED"
    assert row["response_may_be_opened_for_E5"] is False


def test_ecuador_candidate_requires_event_core_only_child_precheck():
    value = _read()
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "ecuador_landscape_camera_2023"
    )
    assert row["public_metadata"]["dwca_event_core_records"] == 958
    assert row["public_metadata"]["dwca_occurrence_extension_records"] == 78299
    assert row["public_metadata"]["event_occurrence_tables_separated"] is True
    assert row["public_metadata"]["visits_per_selected_grid"] == 2
    assert row["public_metadata"]["selected_landscapes"] == 5
    assert row["public_metadata"]["public_temporal_coverage"] == "2015-10-22 to 2018-01-27"
    assert row["gates"]["G2_SCHEMA_EFFORT_TIME"] == "PARTIAL_EVENT_CORE_PASS_RESPONSE_SCHEMA_UNOPENED"
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"] == "UNRESOLVED_REPEAT_VISIT_PATH_NOT_IDENTIFIED"
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert row["response_may_be_opened_for_E5"] is False
    assert "next_response_blind_check" not in row
