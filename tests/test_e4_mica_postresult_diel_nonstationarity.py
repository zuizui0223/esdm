from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_DIEL_NONSTATIONARITY_SUPPLEMENT.json"
)


def _read() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e4_diel_nonstationarity_supplement_is_postresult_only():
    value = _read()
    boundary = value["analysis_boundary"]

    assert value["status"] == "POSTRESULT_EXPLORATORY_SUPPLEMENT"
    assert value["source_result"]["workflow_run_id"] == 36622802225
    assert value["source_result"]["artifact_id"] == 11059622869
    assert boundary["new_model_fit"] is False
    assert boundary["posterior_refit"] is False
    assert boundary["retuning"] is False
    assert boundary["backend_switch"] is False
    assert boundary["laplace_or_inla"] is False
    assert boundary["claim_promotion"] is False
    assert boundary["frozen_e4_result_changed"] is False


def test_e4_weaker_diel_contrast_persists_within_seasons():
    value = _read()["season_stratified_diel_rates"]

    assert value["winter"]["training"]["night_day_rate_ratio"] > 6.0
    assert value["winter"]["D_MICA"]["night_day_rate_ratio"] < 4.0

    assert value["spring"]["training"]["night_day_rate_ratio"] > 60.0
    assert value["spring"]["D_MICA"]["night_day_rate_ratio"] < 3.0

    assert value["summer"]["training"]["night_day_rate_ratio"] is None
    assert value["summer"]["training"]["day_events"] == 0
    assert 2.0 < value["summer"]["D_MICA"]["night_day_rate_ratio"] < 3.0

    assert value["autumn"]["training"]["night_day_rate_ratio"] > 12.0
    assert value["autumn"]["D_MICA"]["night_day_rate_ratio"] < 4.0


def test_e4_simple_event_definition_shift_is_not_supported():
    value = _read()["event_generation_checks"]

    assert value["cameraDelay"]["training_state_annotated"].startswith("0 for 266/266")
    assert value["cameraDelay"]["D_MICA"].startswith("0 for 163/163")
    assert value["event_duration_seconds"]["training_median"] == 6.0
    assert value["event_duration_seconds"]["D_MICA_median"] == 6.0
    assert value["observation_rows_per_event_mean"]["training"] < 1.01
    assert value["observation_rows_per_event_mean"]["D_MICA"] < 1.01


def test_e4_d_mica_events_are_more_temporally_clustered_but_mechanism_stays_open():
    value = _read()["within_deployment_temporal_clustering"]

    assert value["events_per_active_day_mean"]["D_MICA"] > value["events_per_active_day_mean"]["training"]
    assert value["median_interevent_interval_seconds"]["D_MICA"] < value["median_interevent_interval_seconds"]["training"]
    assert value["fraction_interevent_intervals_below_30_minutes"]["D_MICA"] > value["fraction_interevent_intervals_below_30_minutes"]["training"]


def test_e4_frozen_activity_model_lacks_diel_nonstationarity_interactions():
    value = _read()
    model = value["model_structure_diagnostic"]
    future = value["future_independent_hypothesis"]

    assert model["season_by_diurnal_interaction_present"] is False
    assert model["region_by_diurnal_interaction_present"] is False
    assert model["random_location_activity_profile_present"] is False
    assert future["e4_reanalysis_authorized"] is False
    assert "new independent data" in future["required_test_design"][0]
