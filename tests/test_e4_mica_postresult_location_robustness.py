from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_LOCATION_ROBUSTNESS_SUPPLEMENT.json"
)


def _read() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e4_location_robustness_is_postresult_only():
    value = _read()
    boundary = value["analysis_boundary"]

    assert value["status"] == "POSTRESULT_EXPLORATORY_SUPPLEMENT"
    assert value["source_result"]["workflow_run_id"] == 36622802225
    assert value["source_result"]["artifact_id"] == 11059622869
    assert value["source_result"]["heldout_deployment_rows"] == 733
    assert boundary["new_model_fit"] is False
    assert boundary["posterior_refit"] is False
    assert boundary["retuning"] is False
    assert boundary["backend_switch"] is False
    assert boundary["laplace_or_inla"] is False
    assert boundary["claim_promotion"] is False
    assert boundary["frozen_e4_result_changed"] is False
    assert boundary["alternative_primary_endpoint"] is False


def test_e4_activity_direction_survives_equal_location_weighting():
    value = _read()
    geometry = value["physical_location_geometry"]
    equal = value["equal_location_weighting"]

    assert geometry["heldout_deployments"] == 733
    assert geometry["unique_location_ids"] == 27
    assert geometry["event_bearing_locations"] == 20
    assert geometry["zero_event_locations"] == 7
    assert geometry["deployments_per_location_median"] == 26

    activity = equal["activity_gain"]
    assert activity["mean"] < -0.75
    assert activity["negative_locations"] == 19
    assert activity["positive_locations"] == 8

    event = equal["event_bearing_locations_only"]
    assert event["activity_negative_locations"] == 19
    assert event["activity_positive_locations"] == 1
    assert event["activity_gain_mean"] < -1.0


def test_e4_activity_direction_survives_every_single_location_deletion():
    loo = _read()["leave_one_location_out"]

    assert loo["locations_tested"] == 27
    assert loo["all_deployment_weighted_activity_means_negative"] is True
    assert loo["minimum_remaining_activity_gain_mean"] < 0.0
    assert loo["maximum_remaining_activity_gain_mean"] < 0.0
    assert loo["least_negative_after_removing_location_name"] == "D_MICA 324"


def test_e4_activity_magnitude_is_domain_concentrated_without_redefining_endpoint():
    value = _read()["source_domain_magnitude"]
    d = value["D_prefix"]
    non_d = value["non_D_event_bearing_locations"]

    assert d["locations"] == 8
    assert d["event_bearing_locations"] == 8
    assert d["locations_with_negative_mean_activity_gain"] == 8
    assert d["deployment_rows"] == 164
    assert d["remaining_deployment_rows_if_excluded"] == 569
    assert -0.004 < d["remaining_deployment_weighted_activity_gain_mean_if_excluded"] < -0.003

    assert non_d["locations"] == 12
    assert non_d["negative_activity_locations"] == 11
    assert non_d["positive_activity_locations"] == 1
