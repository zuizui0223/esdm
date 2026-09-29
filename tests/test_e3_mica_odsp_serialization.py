from __future__ import annotations

import pytest

from esdm.transfer import (
    build_e3_mica_activity_odsp_bundle,
    build_e3_mica_state_odsp_bundle,
)


def _result():
    rows = []
    for index in range(733):
        rows.append(
            {
                "deploymentID": f"dep-{index:04d}",
                "full_heldout_log_score": -1.0 + index * 1e-5,
                "activity_knockout_heldout_log_score": -1.1 + index * 1e-5,
                "state_knockout_heldout_log_score": -1.2 + index * 1e-5,
                "scored_state_context_cells": 8,
            }
        )
    return {
        "schema_version": 1,
        "result_id": "e3-mica-reduced-exploratory-result-v1",
        "programme_id": "E3_MICA_EXP",
        "endpoint_id": "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION",
        "status": "E3_EXPLORATORY_RESULT",
        "scores": {
            "full_heldout_log_score": -0.99,
            "activity_knockout_heldout_log_score": -1.09,
            "state_knockout_heldout_log_score": -1.19,
            "activity_gain": 0.10,
            "state_gain": 0.20,
        },
        "heldout_deployment_scores": rows,
        "decision": {
            "sampling_gate_passed": True,
            "confirmatory_replication_claim": False,
            "e2_rescue": False,
        },
        "response_boundary": {
            "biological_response_already_consumed_under_e2": True,
            "model_fits": 3,
            "heldout_scores": 3,
            "state_calibration_stream_present_in_fit": False,
        },
    }


def test_e3_activity_export_is_parallel_two_level_descriptive_bundle():
    bundle = build_e3_mica_activity_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_e3_mica_activity_transfer_v1"
    assert bundle.contract["evaluation"]["analysis_mode"] == "descriptive"
    assert bundle.contract["columns"]["group"] == "group"
    assert bundle.contract["columns"]["block"] == "block"
    assert bundle.contract["columns"]["population_cluster"] is None
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_state",
            "information": ["suitability", "state"],
            "score_column": "score__suitability_state",
        },
        {
            "name": "suitability_state_activity",
            "information": ["suitability", "state", "activity"],
            "score_column": "score__suitability_state_activity",
        },
    ]
    assert len(bundle.rows) == 733
    assert {row["group"] for row in bundle.rows} == {"MICA_MUSKRAT"}
    assert len({row["block"] for row in bundle.rows}) == 733
    assert bundle.rows[0]["row_id"] == bundle.rows[0]["block"] == "dep-0000"
    assert bundle.rows[0]["score__suitability_state"] == pytest.approx(-1.1)
    assert bundle.rows[0]["score__suitability_state_activity"] == pytest.approx(-1.0)


def test_e3_state_export_is_parallel_not_ordered_after_activity():
    bundle = build_e3_mica_state_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_e3_mica_state_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_activity",
            "information": ["suitability", "activity"],
            "score_column": "score__suitability_activity",
        },
        {
            "name": "suitability_activity_state",
            "information": ["suitability", "activity", "state"],
            "score_column": "score__suitability_activity_state",
        },
    ]
    assert bundle.rows[0]["score__suitability_activity"] == pytest.approx(-1.2)
    assert bundle.rows[0]["score__suitability_activity_state"] == pytest.approx(-1.0)


def test_e3_export_requires_completed_sampling_pass_and_reduced_endpoint():
    broken = _result()
    broken["status"] = "E3_EXPLORATORY_SAMPLING_STOP"
    with pytest.raises(ValueError, match="completed exploratory result"):
        build_e3_mica_activity_odsp_bundle(broken)

    broken = _result()
    broken["decision"]["sampling_gate_passed"] = False
    with pytest.raises(ValueError, match="sampling_gate_passed"):
        build_e3_mica_activity_odsp_bundle(broken)

    broken = _result()
    broken["response_boundary"]["state_calibration_stream_present_in_fit"] = True
    with pytest.raises(ValueError, match="without state calibration"):
        build_e3_mica_state_odsp_bundle(broken)


def test_e3_export_requires_exact_733_unique_deployment_rows():
    broken = _result()
    broken["heldout_deployment_scores"] = broken["heldout_deployment_scores"][:-1]
    with pytest.raises(ValueError, match="exactly 733"):
        build_e3_mica_activity_odsp_bundle(broken)

    broken = _result()
    broken["heldout_deployment_scores"][1]["deploymentID"] = "dep-0000"
    with pytest.raises(ValueError, match="unique non-empty"):
        build_e3_mica_state_odsp_bundle(broken)
