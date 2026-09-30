from __future__ import annotations

import pytest

from esdm.validate.e5_candidate import qualify_e5_candidate_metadata


def _base():
    return {
        "candidate_id": "synthetic-metadata-only",
        "response_firewall": {
            "focal_response_opened": False,
            "response_values_used_for_selection": False,
        },
        "independence": {
            "new_response_dataset": True,
            "not_mica_derivative": True,
            "not_snapshot_japan_derivative": True,
        },
        "schema": {
            "deployment_id": True,
            "physical_location_id": True,
            "effort_interval": True,
            "event_time_schema": True,
            "taxon_identity": True,
            "geography": True,
            "source_or_protocol": True,
        },
        "crossed_domain": {"qualified_crossing": True},
        "detection": {"separately_identifiable_effective_detection": True},
        "physical_replication": {
            "repeated_deployments_nested_under_location": True,
            "training_independent_locations": 20,
            "heldout_independent_locations": 10,
            "heldout_training_location_overlap": 0,
        },
        "temporal_support": {
            "training_distinct_calendar_months": 6,
            "heldout_distinct_calendar_months": 6,
            "training_has_day_and_night_effort": True,
            "heldout_has_day_and_night_effort": True,
            "seasonal_coverage_overlaps": True,
        },
        "model_freeze": {
            "activity_detection_structure_frozen": True,
            "geography_or_source_by_diel_frozen": True,
            "season_by_diel_frozen": True,
        },
    }


def test_e5_metadata_evaluator_requires_all_seven_gates():
    result = qualify_e5_candidate_metadata(_base())
    assert result["status"] == "E5_CANDIDATE_QUALIFIED_PRE_RESPONSE"
    assert result["all_pre_response_gates_passed"] is True
    assert list(result["gates"]) == [
        "G1_INDEPENDENT_SOURCE",
        "G2_SCHEMA_EFFORT_TIME",
        "G3_CROSSED_DOMAIN",
        "G4_DETECTION_IDENTIFIABILITY",
        "G5_PHYSICAL_REPLICATION",
        "G6_TEMPORAL_SUPPORT",
        "G7_MODEL_FREEZE",
    ]
    assert result["response_boundary"]["focal_response_opening_authorized"] is False
    assert result["response_boundary"]["model_fitting_authorized"] is False


def test_e5_snapshot_usa_like_five_month_candidate_fails_g6():
    manifest = _base()
    manifest["candidate_id"] = "snapshot-usa-2024-like"
    manifest["temporal_support"]["training_distinct_calendar_months"] = 5
    manifest["temporal_support"]["heldout_distinct_calendar_months"] = 5

    result = qualify_e5_candidate_metadata(manifest)
    assert result["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert result["gates"]["G6_TEMPORAL_SUPPORT"]["passed"] is False


def test_e5_sunda_like_unverified_event_schema_fails_g2():
    manifest = _base()
    manifest["candidate_id"] = "sunda-like"
    manifest["schema"]["event_time_schema"] = False

    result = qualify_e5_candidate_metadata(manifest)
    assert result["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert result["gates"]["G2_SCHEMA_EFFORT_TIME"]["passed"] is False


def test_e5_location_minima_and_overlap_fail_closed():
    manifest = _base()
    manifest["physical_replication"]["training_independent_locations"] = 19
    manifest["physical_replication"]["heldout_training_location_overlap"] = 1

    result = qualify_e5_candidate_metadata(manifest)
    assert result["gates"]["G5_PHYSICAL_REPLICATION"]["passed"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("focal_response_opened", True),
        ("response_values_used_for_selection", True),
        ("focal_response_opened", None),
    ],
)
def test_e5_evaluator_refuses_response_contamination(key, value):
    manifest = _base()
    manifest["response_firewall"][key] = value
    with pytest.raises(ValueError):
        qualify_e5_candidate_metadata(manifest)
