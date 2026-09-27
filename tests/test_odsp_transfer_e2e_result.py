from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "ODSP_TRANSFER_E2E_RESULT_V1.json"


def _read() -> dict[str, object]:
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_integration_result_pins_exact_successful_cross_repo_run():
    result = _read()
    integration = result["integration"]

    assert integration["integration_merge_sha"] == (
        "3f939082d8509553f5e2a95ebb9ea58f46b40859"
    )
    assert integration["workflow_run_id"] == 36070032488
    assert integration["run_attempt"] == 1
    assert integration["conclusion"] == "success"
    assert integration["artifact_id"] == 10837529197
    assert integration["artifact_digest"] == (
        "sha256:655af1311a8d9f5d9cb910ca5ccf3a50e6caede73474dba8ab2fd7ffb5840af8"
    )
    assert integration["pinned_odsp_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_integration_reproduces_frozen_esdm_mean_exactly_in_odsp():
    result = _read()
    odsp = result["odsp_result"]

    assert odsp["population_group_count"] == 16
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_gain"] == 0.36244191577864204
    assert odsp["population_mean_interval"][0] > 0
    assert odsp["population_status"] == "positive"
    assert odsp["point_transfer_ceiling"] == "suitability_accessibility"
    assert odsp["population_mean_supported_ceiling"] == "suitability_accessibility"


def test_legacy_certification_failure_does_not_erase_population_value():
    result = _read()
    odsp = result["odsp_result"]

    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["certification_estimable_cell_count"] == 0
    assert odsp["certification_cell_count"] == 16
    assert odsp["certified_transfer_ceiling"] == "suitability_only"
    assert odsp["population_status"] == "positive"


def test_n3_value_retains_uncertainty_and_cannot_become_survey_action():
    result = _read()
    value = result["n3_transfer_value"]
    prediction_lower, prediction_upper = result["odsp_result"]["prediction_interval"]

    assert value["total_expected_gain"] == 0.36244191577864204
    assert value["total_conservative_mean_value"] == 0.27041044003054493
    assert value["total_conservative_mean_value"] > 0
    assert prediction_lower < 0 < prediction_upper
    assert value["score"]["unit"] == "nats_per_heldout_context"
    assert value["authorizes_state_promotion"] is False
    assert value["authorizes_spatial_patch_ranking"] is False
    assert value["authorizes_survey_site_selection"] is False
    assert value["authorizes_n4_action"] is False
    assert value["n4_survey_action_owner"] == "ACSP"


def test_all_integration_output_hashes_are_pinned():
    hashes = _read()["output_hashes"]
    assert set(hashes) == {
        "scores.csv",
        "endpoint.json",
        "adapter_manifest.json",
        "receipt.json",
        "N2_TO_N3_TRANSFER_VALUE_PAYLOAD.json",
    }
    assert all(len(value) == 64 for value in hashes.values())
