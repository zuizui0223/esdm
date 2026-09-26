from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "ODSP_TRANSFER_R5B_PARALLEL_BINDING_V1.json"


def _read():
    return json.loads(BINDING.read_text(encoding="utf-8"))


def test_r5b_parallel_binding_pins_exact_frozen_source_and_odsp():
    binding = _read()

    assert binding["source"]["workflow_run_id"] == 35879936964
    assert binding["source"]["artifact_id"] == 10761956596
    assert binding["source"]["artifact_digest"] == (
        "sha256:ead0e17a4da17b3c27b84bcbb0c4aa034379f9930ce32987e1940215ba839477"
    )
    assert binding["source"]["result_sha256"] == (
        "65580510b56076ecd0d8f893af991a930eb50ba055b060ce11d78d0f2646c2e0"
    )
    assert binding["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_activity_and_state_are_parallel_not_one_ordered_filtration():
    binding = _read()
    activity = binding["contrasts"]["activity"]
    state = binding["contrasts"]["state"]
    boundary = binding["ordering_boundary"]

    assert activity["lower"]["information"] == ["suitability", "state"]
    assert activity["upper"]["information"] == ["suitability", "state", "activity"]
    assert state["lower"]["information"] == ["suitability", "activity"]
    assert state["upper"]["information"] == ["suitability", "activity", "state"]

    assert boundary["activity_and_state_have_natural_order"] is False
    assert boundary["combined_three_level_filtration_authorized"] is False


def test_r5b_activity_expected_population_result_is_positive():
    activity = _read()["contrasts"]["activity"]

    assert activity["source_summary"]["replicates"] == 16
    assert activity["source_summary"]["positive_gain_rate"] == 1.0
    assert activity["source_summary"]["mean_gain"] == 0.00699856015906225
    assert activity["source_summary"]["minimum_gain"] > 0

    expected = activity["expected_odsp"]
    assert expected["population_mean_interval"][0] > 0
    assert expected["population_status"] == "positive"
    assert expected["population_ceiling"] == "suitability_state_activity"
    assert expected["certified_ceiling"] == "suitability_state"
    assert expected["certification_all_steps_estimable"] is False
    assert expected["prediction_interval"][0] > 0


def test_r5b_state_expected_population_result_is_positive():
    state = _read()["contrasts"]["state"]

    assert state["source_summary"]["replicates"] == 16
    assert state["source_summary"]["positive_gain_rate"] == 1.0
    assert state["source_summary"]["mean_gain"] == 0.02896466849576273
    assert state["source_summary"]["minimum_gain"] > 0

    expected = state["expected_odsp"]
    assert expected["population_mean_interval"][0] > 0
    assert expected["population_status"] == "positive"
    assert expected["population_ceiling"] == "suitability_activity_state"
    assert expected["certified_ceiling"] == "suitability_activity"
    assert expected["certification_all_steps_estimable"] is False
    assert expected["prediction_interval"][0] > 0


def test_r5b_n3_currency_and_action_boundary_are_shared_but_values_are_separate():
    binding = _read()
    common = binding["common_n3_handoff"]
    activity = binding["contrasts"]["activity"]
    state = binding["contrasts"]["state"]

    assert common["score_kind"] == "log"
    assert common["score_unit"] == "nats_per_heldout_state_block_context"
    assert common["authorizes_spatial_patch_ranking"] is False
    assert common["authorizes_survey_site_selection"] is False
    assert common["n4_survey_action_owner"] == "ACSP"

    assert activity["n3"]["expected_conservative_mean_value"] > 0
    assert state["n3"]["expected_conservative_mean_value"] > 0
    assert (
        activity["n3"]["expected_conservative_mean_value"]
        != state["n3"]["expected_conservative_mean_value"]
    )


def test_r5b_parallel_audit_does_not_reopen_science_or_eog():
    boundary = _read()["scientific_boundary"]

    assert boundary["reopens_r5b_gate"] is False
    assert boundary["changes_r5b_promotion"] is False
    assert boundary["new_empirical_biological_claim"] is False
    assert boundary["causal_activity_claim"] is False
    assert boundary["causal_state_claim"] is False
    assert boundary["current_eog_mainline_consumer_authorized"] is False
