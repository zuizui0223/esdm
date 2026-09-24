from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "ODSP_TRANSFER_E2E_BINDING_V1.json"


def _read() -> dict[str, object]:
    return json.loads(BINDING.read_text(encoding="utf-8"))


def test_e2e_binding_pins_exact_source_and_odsp_commits():
    binding = _read()

    assert binding["source"]["workflow_run_id"] == 35989902607
    assert binding["source"]["artifact_id"] == 10804831269
    assert binding["source"]["artifact_digest"] == (
        "sha256:978a10cbd9c6d0fcd382a925b47e6311e26658ad5c91c8ec9b2a50f4442b73e5"
    )
    assert binding["source"]["result_sha256"] == (
        "243f90c6a246fa020043873ae63f4c14adb08999009392767644bc529c6341cc"
    )
    assert binding["source"]["adapter_merge_sha"] == (
        "e9bec1be8136a85c265af3604394d3389319998d"
    )
    assert binding["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_e2e_binding_preserves_nested_accessibility_filtration():
    binding = _read()
    levels = binding["information_filtration"]

    assert levels == [
        {
            "name": "suitability_only",
            "information": ["suitability"],
            "source_score": "accessibility_knockout_heldout_log_score",
        },
        {
            "name": "suitability_accessibility",
            "information": ["suitability", "accessibility"],
            "source_score": "full_heldout_log_score",
        },
    ]


def test_e2e_expected_population_result_matches_frozen_esdm_summary():
    binding = _read()
    source = binding["expected_source_summary"]
    odsp = binding["expected_odsp_behavior"]

    assert source["replicates"] == 16
    assert source["positive_gain_rate"] == 1.0
    assert source["mean_gain"] == 0.36244191577864204
    assert source["minimum_gain"] > 0

    assert odsp["population_group_count"] == 16
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_gain"] == source["mean_gain"]
    assert odsp["population_status"] == "positive"
    assert odsp["point_transfer_ceiling"] == "suitability_accessibility"
    assert odsp["population_transfer_ceiling"] == "suitability_accessibility"


def test_legacy_certification_and_population_estimand_are_expected_to_differ():
    binding = _read()
    odsp = binding["expected_odsp_behavior"]

    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["certified_transfer_ceiling"] == "suitability_only"
    assert "minimum-block" in odsp["reason_certification_stops"]


def test_e2e_handoff_never_authorizes_survey_action():
    handoff = _read()["n3_handoff"]

    assert handoff["schema_id"] == "n2-to-n3-transfer-value-payload-v1"
    assert handoff["score_kind"] == "log"
    assert handoff["score_unit"] == "nats_per_heldout_context"
    assert handoff["expected_conservative_value_positive"] is True
    assert handoff["authorizes_spatial_patch_ranking"] is False
    assert handoff["authorizes_survey_site_selection"] is False
    assert handoff["n4_survey_action_owner"] == "ACSP"


def test_e2e_is_integration_only_not_new_scientific_gate():
    boundary = _read()["scientific_boundary"]

    assert boundary["reopens_v06a_gate"] is False
    assert boundary["changes_v06a_promotion"] is False
    assert boundary["changes_odsp_inference"] is False
    assert boundary["empirical_biological_claim"] is False
