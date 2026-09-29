from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.freeze_e3_mica_reduced_result import freeze_result


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "replication"
    / "E3_MICA_REDUCED_RESULT_IMPORT_CONTRACT.json"
)


def _row(i, full=-1.0, activity=-1.2, state=-1.1):
    return {
        "deploymentID": f"d-{i:04d}",
        "full_heldout_log_score": full,
        "activity_knockout_heldout_log_score": activity,
        "state_knockout_heldout_log_score": state,
        "scored_state_context_cells": 10,
    }


def _result():
    rows = [_row(i) for i in range(733)]
    return {
        "schema_version": 1,
        "result_id": "e3-mica-reduced-exploratory-result-v1",
        "programme_id": "E3_MICA_EXP",
        "endpoint_id": "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION",
        "status": "E3_EXPLORATORY_RESULT",
        "capture_fixture_fingerprint_sha256": (
            "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
        ),
        "fit_contract_id": "e3-mica-reduced-exploratory-fit-v1",
        "scores": {
            "full_heldout_log_score": -1.0,
            "activity_knockout_heldout_log_score": -1.2,
            "state_knockout_heldout_log_score": -1.1,
            "activity_gain": 0.2,
            "state_gain": 0.1,
        },
        "divergences": {
            "full": 0,
            "activity_knockout": 0,
            "state_knockout": 0,
            "total": 0,
        },
        "heldout_deployment_scores": rows,
        "odsp_serialization": {
            "row_count": 733,
            "row_unit": "one east-heldout deployment",
            "absolute_scores_serialized": True,
            "gain_only_serialization": False,
            "same_scored_cells_across_models": True,
        },
        "decision": {
            "sampling_gate_passed": True,
            "activity_predictive_support_descriptive": True,
            "state_predictive_support_descriptive": True,
            "minimum_effect_size_threshold": None,
            "confirmatory_replication_claim": False,
            "e2_rescue": False,
            "causal_claim_authorized": False,
            "parameter_recovery_claim_authorized": False,
            "same_programme_rerun_allowed": False,
        },
    }


def _write(tmp_path, payload):
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_import_contract_binds_the_single_authorized_run():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    execution = contract["authorized_execution"]

    assert contract["status"] == "FROZEN_PRE_RESULT_IMPORT"
    assert execution["workflow_run_id"] == 36522315963
    assert execution["run_attempt"] == 1
    assert execution["authorization_head_sha"] == (
        "65300be9ab5ea25cbd321011c6e4ca1db7efc5f3"
    )
    assert contract["import_rule"]["failed_or_negative_result_must_be_frozen"] is True
    assert contract["import_rule"]["post_result_threshold_retuning_allowed"] is False


def test_valid_scored_result_freezes_without_reinterpretation(tmp_path):
    path = _write(tmp_path, _result())
    receipt = freeze_result(
        path,
        artifact_id=123,
        artifact_name="result",
        artifact_digest="sha256:abc",
    )

    assert receipt["status"] == "E3_EXPLORATORY_RESULT"
    assert receipt["summary"]["heldout_row_count"] == 733
    assert receipt["summary"]["divergences"]["total"] == 0
    assert receipt["summary"]["scores"]["activity_gain"] == pytest.approx(0.2)
    assert receipt["terminal_rule"]["same_programme_rerun_allowed"] is False


def test_duplicate_heldout_deployment_fails_closed(tmp_path):
    payload = _result()
    payload["heldout_deployment_scores"][1]["deploymentID"] = (
        payload["heldout_deployment_scores"][0]["deploymentID"]
    )
    path = _write(tmp_path, payload)

    with pytest.raises(ValueError, match="unique non-empty"):
        freeze_result(
            path,
            artifact_id=123,
            artifact_name="result",
            artifact_digest="sha256:abc",
        )


def test_negative_gain_is_importable_and_not_retuned(tmp_path):
    payload = _result()
    payload["scores"]["activity_knockout_heldout_log_score"] = -0.8
    payload["scores"]["activity_gain"] = -0.2
    for row in payload["heldout_deployment_scores"]:
        row["activity_knockout_heldout_log_score"] = -0.8
    payload["decision"]["activity_predictive_support_descriptive"] = False
    path = _write(tmp_path, payload)

    receipt = freeze_result(
        path,
        artifact_id=123,
        artifact_name="result",
        artifact_digest="sha256:abc",
    )
    assert receipt["summary"]["scores"]["activity_gain"] == pytest.approx(-0.2)
    assert receipt["terminal_rule"]["post_result_threshold_retuning_allowed"] is False
