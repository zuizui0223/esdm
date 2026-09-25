from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "ODSP_TRANSFER_V07B_E2E_BINDING_V1.json"


def _read():
    return json.loads(BINDING.read_text(encoding="utf-8"))


def test_v07b_binding_pins_exact_frozen_result_and_odsp_commit():
    binding = _read()

    assert binding["source"]["workflow_run_id"] == 36074930922
    assert binding["source"]["artifact_id"] == 10840405228
    assert binding["source"]["artifact_digest"] == (
        "sha256:a5b2bed48b3acadc8b7c7461dd13074007d34e39a3a5ccfb303b984ff7c5d247"
    )
    assert binding["source"]["result_sha256"] == (
        "c3a5c51b9d8ccbb422b0181ad93d9dc4b1cb405668667e30b4ede0ccb3fef32b"
    )
    assert binding["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_v07b_binding_preserves_dynamic_occupancy_information_filtration():
    binding = _read()
    assert binding["information_filtration"] == [
        {
            "name": "suitability_only",
            "information": ["suitability"],
            "source_score": "occupancy_knockout_heldout_log_score",
        },
        {
            "name": "suitability_dynamic_occupancy",
            "information": ["suitability", "dynamic_occupancy"],
            "source_score": "full_heldout_log_score",
        },
    ]


def test_v07b_expected_odsp_population_result_matches_frozen_summary():
    binding = _read()
    source = binding["expected_source_summary"]
    odsp = binding["expected_odsp_behavior"]

    assert source["replicates"] == 16
    assert source["positive_gain_rate"] == 1.0
    assert source["mean_gain"] == 7.090827989764034
    assert source["minimum_gain"] > 0

    assert odsp["population_group_count"] == 16
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_gain"] == source["mean_gain"]
    assert odsp["population_mean_interval"][0] > 0
    assert odsp["population_status"] == "positive"
    assert odsp["point_transfer_ceiling"] == "suitability_dynamic_occupancy"
    assert odsp["population_transfer_ceiling"] == "suitability_dynamic_occupancy"


def test_v07b_binding_keeps_legacy_certification_separate():
    odsp = _read()["expected_odsp_behavior"]

    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["certification_estimable_cell_count"] == 0
    assert odsp["certification_cell_count"] == 16
    assert odsp["certified_transfer_ceiling"] == "suitability_only"


def test_v07b_n3_handoff_is_value_only_not_action():
    handoff = _read()["n3_handoff"]

    assert handoff["schema_id"] == "n2-to-n3-transfer-value-payload-v1"
    assert handoff["score_kind"] == "log"
    assert handoff["score_unit"] == "nats_per_heldout_context"
    assert handoff["expected_total_status"] == "positive"
    assert handoff["expected_conservative_mean_value"] > 0
    assert handoff["authorizes_spatial_patch_ranking"] is False
    assert handoff["authorizes_survey_site_selection"] is False
    assert handoff["n4_survey_action_owner"] == "ACSP"


def test_v07b_odsp_integration_is_not_new_scientific_promotion():
    boundary = _read()["scientific_boundary"]

    assert boundary["reopens_v07b_gate"] is False
    assert boundary["changes_v07b_promotion"] is False
    assert boundary["changes_odsp_inference"] is False
    assert boundary["empirical_biological_claim"] is False
    assert boundary["movement_kernel_claim"] is False
    assert boundary["current_eog_mainline_consumer_authorized"] is False
