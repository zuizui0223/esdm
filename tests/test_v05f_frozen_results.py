from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V05F_FROZEN_RESULTS.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_v05f_frozen_result_is_single_completed_scientific_fail():
    result = _read()

    assert result["status"] == "FAIL"
    assert result["execution"]["workflow_run_id"] == 36107440569
    assert result["execution"]["run_attempt"] == 1
    assert result["execution"]["outcome_head_sha"] == (
        "bb1e2fd6a18eb9905608a894f3329d8c9bffe16f"
    )
    assert result["execution"]["qualification_passed"] is True
    assert result["execution"]["all_32_replicates_completed"] is True
    assert result["execution"]["infrastructure_block"] is None
    assert result["execution"]["result_artifact_id"] == 10851963085
    assert result["execution"]["result_json_sha256"] == (
        "169d7589395b013dec37a95cfc1b273d966434a9a430a5f05a9a6fd20994b931"
    )


def test_v05f_interaction_world_replicates_but_null_specificity_fails():
    result = _read()
    interaction = result["summary"]["interaction"]
    null = result["summary"]["measured_shared_null"]
    failed = result["failed_check"]

    assert interaction["positive_gain_rate"] == 1.0
    assert interaction["material_gain_rate"] == 1.0
    assert interaction["mean_heldout_gain"] == 1.1190587549523654
    assert interaction["coverage"] == 0.9375
    assert abs(interaction["mean_bias"]) <= 0.15

    assert null["mean_heldout_gain"] < 0
    assert null["coverage"] == 1.0
    assert null["nonzero_interval_rate"] == 0.0
    assert null["material_gain_rate"] == 0.3125
    assert null["material_gain_count"] == 5
    assert null["allowed_material_gain_count"] == 4

    assert failed == {
        "name": "null_material_gain_rate",
        "observed": 0.3125,
        "criterion": "<= 0.25",
        "observed_count": 5,
        "maximum_allowed_count": 4,
        "other_frozen_checks_passed": 18,
    }


def test_v05f_absolute_score_serialization_passes_but_cannot_rescue_gate():
    result = _read()
    serialization = result["absolute_score_serialization"]
    decision = result["decision"]

    assert serialization["passed"] is True
    assert serialization["max_abs_gain_identity_error"] == 0.0
    assert serialization["generated_odsp_bundle"] is True
    assert len(serialization["adapter_manifest_sha256"]) == 64
    assert len(serialization["endpoint_json_sha256"]) == 64
    assert len(serialization["scores_csv_sha256"]) == 64

    assert decision["pass"] is False
    assert decision["retune_allowed"] is False
    assert decision["rerun_same_v05f_allowed"] is False
    assert decision["original_v05a_reopened"] is False
    assert decision["odsp_validated_export_authorized"] is False
    assert decision["n3_transfer_value_authorized"] is False


def test_v05f_fail_does_not_expand_interaction_claim():
    interpretation = _read()["interpretation"]

    assert "v0.5f replication PASS" in interpretation["not_supported"]
    assert "hidden-common-driver robustness" in interpretation["not_supported"]
    assert "causal interaction in empirical data" in interpretation["not_supported"]
    assert "EOG consumption or N4 action" in interpretation["not_supported"]
