from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "ODSP_TRANSFER_V07B_E2E_RESULT_V1.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_v07b_odsp_result_pins_exact_successful_integration_run():
    result = _read()
    integration = result["integration"]

    assert integration["validation_head_sha"] == (
        "41d920e4f71da2f922076477da9b6ca906571eaf"
    )
    assert integration["workflow_run_id"] == 36076828551
    assert integration["run_attempt"] == 1
    assert integration["conclusion"] == "success"
    assert integration["artifact_id"] == 10839833749
    assert integration["artifact_digest"] == (
        "sha256:62d54dae86dd26923a75580cfd14bfc3865546d052b3f04065f008d68b5c9180"
    )
    assert integration["pinned_odsp_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_v07b_odsp_population_result_preserves_dynamic_gain():
    result = _read()
    odsp = result["odsp_result"]

    assert odsp["population_group_count"] == 16
    assert odsp["population_positive_group_count"] == 16
    assert odsp["population_positive_group_fraction"] == 1.0
    assert odsp["population_mean_gain"] == 7.090827989764035
    assert odsp["population_mean_interval"][0] > 0
    assert odsp["population_status"] == "positive"
    assert odsp["point_transfer_ceiling"] == "suitability_dynamic_occupancy"
    assert (
        odsp["population_mean_supported_ceiling"]
        == "suitability_dynamic_occupancy"
    )


def test_v07b_legacy_certification_is_separate_from_population_value():
    odsp = _read()["odsp_result"]

    assert odsp["certification_all_steps_estimable"] is False
    assert odsp["certification_estimable_cell_count"] == 0
    assert odsp["certification_cell_count"] == 16
    assert odsp["certified_transfer_ceiling"] == "suitability_only"
    assert odsp["population_status"] == "positive"


def test_v07b_n3_transfer_value_is_positive_but_not_action_authority():
    value = _read()["n3_transfer_value"]

    assert value["total_expected_gain"] == 7.090827989764035
    assert value["total_conservative_mean_value"] == 6.112566461456692
    assert value["total_status"] == "positive"
    assert value["prediction_interval"][0] > 0
    assert value["score"]["unit"] == "nats_per_heldout_context"
    assert value["authorizes_state_promotion"] is False
    assert value["authorizes_spatial_patch_ranking"] is False
    assert value["authorizes_survey_site_selection"] is False
    assert value["authorizes_n4_action"] is False
    assert value["n4_survey_action_owner"] == "ACSP"


def test_v07b_integration_output_hashes_are_frozen():
    hashes = _read()["output_hashes"]

    assert set(hashes) == {
        "scores.csv",
        "endpoint.json",
        "adapter_manifest.json",
        "receipt.json",
        "N2_TO_N3_TRANSFER_VALUE_PAYLOAD_V07B.json",
    }
    assert all(len(value) == 64 for value in hashes.values())


def test_v07b_integration_does_not_expand_claim_to_movement_or_eog():
    interpretation = _read()["interpretation"]

    assert "movement or dispersal kernels" in interpretation["not_supported"]
    assert "survey-site ranking or N4 action" in interpretation["not_supported"]
    assert "use by the frozen current EOG mainline" in interpretation["not_supported"]
