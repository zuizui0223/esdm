from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "ODSP_TRANSFER_R5B_PARALLEL_RESULT_V1.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_parallel_r5b_result_pins_single_successful_integration_run():
    result = _read()
    integration = result["integration"]

    assert integration["validation_head_sha"] == (
        "379f9af9f76811a96d99eaca37371119deb54fef"
    )
    assert integration["workflow_run_id"] == 36077749897
    assert integration["run_attempt"] == 1
    assert integration["conclusion"] == "success"
    assert integration["artifact_id"] == 10841275246
    assert integration["artifact_digest"] == (
        "sha256:6d03a43607261e42e020b3cc73dd652205d72873607584f0ed9b55a1dc748231"
    )


def test_activity_population_value_is_frozen_positive():
    activity = _read()["contrasts"]["activity"]
    odsp = activity["odsp_result"]
    value = activity["n3_transfer_value"]

    assert odsp["population_mean_gain"] == 0.00699856015906225
    assert odsp["population_mean_interval"][0] > 0
    assert odsp["population_status"] == "positive"
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_supported_ceiling"] == (
        "suitability_state_activity"
    )
    assert odsp["certified_transfer_ceiling"] == "suitability_state"
    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["prediction_interval"][0] > 0

    assert value["total_expected_gain"] == odsp["population_mean_gain"]
    assert value["conservative_mean_value"] == odsp["population_mean_interval"][0]
    assert value["prediction_interval"] == odsp["prediction_interval"]


def test_state_population_value_is_frozen_positive():
    state = _read()["contrasts"]["state"]
    odsp = state["odsp_result"]
    value = state["n3_transfer_value"]

    assert odsp["population_mean_gain"] == 0.02896466849576273
    assert odsp["population_mean_interval"][0] > 0
    assert odsp["population_status"] == "positive"
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_supported_ceiling"] == (
        "suitability_activity_state"
    )
    assert odsp["certified_transfer_ceiling"] == "suitability_activity"
    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["prediction_interval"][0] > 0

    assert value["total_expected_gain"] == odsp["population_mean_gain"]
    assert value["conservative_mean_value"] == odsp["population_mean_interval"][0]
    assert value["prediction_interval"] == odsp["prediction_interval"]


def test_parallel_result_does_not_impose_activity_state_order():
    result = _read()

    assert result["ordering_boundary"]["activity_and_state_are_parallel"] is True
    assert (
        result["ordering_boundary"]["combined_three_level_filtration_authorized"]
        is False
    )


def test_parallel_result_preserves_n4_action_boundary():
    boundary = _read()["action_boundary"]

    assert boundary["authorizes_state_promotion"] is False
    assert boundary["authorizes_spatial_patch_ranking"] is False
    assert boundary["authorizes_survey_site_selection"] is False
    assert boundary["authorizes_n4_action"] is False
    assert boundary["n4_survey_action_owner"] == "ACSP"
    assert boundary["current_eog_mainline_consumer_authorized"] is False


def test_parallel_result_hashes_and_fingerprints_are_pinned():
    result = _read()

    for contrast in ("activity", "state"):
        row = result["contrasts"][contrast]
        assert all(len(value) == 64 for value in row["output_hashes"].values())
        assert len(row["n3_transfer_value"]["fingerprint"]) == 64
        assert len(row["n3_transfer_value"]["source_population_fingerprint"]) == 64
