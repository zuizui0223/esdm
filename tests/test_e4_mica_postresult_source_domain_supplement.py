from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_SOURCE_DOMAIN_SUPPLEMENT.json"
)


def _read() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_e4_source_domain_supplement_is_postresult_only():
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
    assert boundary["frozen_e4_result_changed"] is False


def test_e4_source_domain_supplement_locks_physical_location_concentration():
    value = _read()["physical_location_concentration"]

    assert value["heldout_deployments"] == 733
    assert value["heldout_unique_location_names"] == 27
    assert value["D_prefix"]["deployments"] == 164
    assert value["D_prefix"]["unique_location_names"] == 8
    assert value["D_prefix"]["focal_events"] == 5091
    assert value["D_prefix"]["fraction_of_all_heldout_focal_events"] > 0.989
    assert value["D_prefix"]["fraction_of_net_activity_gain_sum"] > 0.996
    assert value["D_MICA_prefix"]["deployments"] == 163
    assert value["D_MICA_prefix"]["unique_location_names"] == 7
    assert value["D_MICA_prefix"]["focal_events"] == 5049
    assert value["D_MICA_prefix"]["fraction_of_net_activity_gain_sum"] > 0.993


def test_e4_source_domain_supplement_locks_metadata_shift_without_causal_claim():
    value = _read()
    deployment = value["deployment_metadata_shift"]
    annotation = value["annotation_metadata_shift"]

    assert deployment["comparison"]["training_state_annotated_deployments"] == 266
    assert deployment["comparison"]["heldout_D_prefix_deployments"] == 164
    assert deployment["cameraHeight_missing"]["training_state_annotated"]["fraction"] < 0.04
    assert deployment["cameraHeight_missing"]["heldout_D_prefix"]["fraction"] > 0.99
    assert deployment["detectionDistance_missing"]["training_state_annotated"]["fraction"] < 0.04
    assert deployment["detectionDistance_missing"]["heldout_D_prefix"]["fraction"] > 0.99
    assert deployment["setupBy"]["heldout_D_prefix_top"]["value"] == "Björn Matthies"
    assert deployment["setupBy"]["heldout_D_prefix_top"]["count"] == 161

    assert annotation["focal_observation_rows"]["training_state_annotated"] == 1340
    assert annotation["focal_observation_rows"]["heldout_D_prefix"] == 5113
    assert annotation["classifiedBy"]["heldout_D_prefix_top"]["value"] == "Heiko Fritz"
    assert annotation["classifiedBy"]["heldout_D_prefix_top"]["count"] == 4957
    assert annotation["lifeStage_nonempty"]["training_state_annotated"]["fraction"] < 0.10
    assert annotation["lifeStage_nonempty"]["heldout_D_prefix"]["fraction"] > 0.94

    forbidden = value["interpretation"]["not_supported"]
    assert "A causal country effect." in forbidden
    assert any("observer" in item for item in forbidden)


def test_e4_source_domain_supplement_records_detection_identifiability_limit():
    value = _read()
    vulnerability = value["observation_model_vulnerability"]

    assert vulnerability["state_annotated_detection"] == "KnownDetection(probability=1.0)"
    assert vulnerability["state_annotated_informs"] == ["activity", "state"]
    assert "cannot identify" in vulnerability["implication"]
    assert "separately" in vulnerability["implication"]
    assert value["calendar_overlap"]["overlap_present"] is True
    assert value["ecological_context"]["training_night_day_event_rate_ratio"] > 13.0
    assert 2.9 < value["ecological_context"]["heldout_D_night_day_event_ratio"] < 3.1
