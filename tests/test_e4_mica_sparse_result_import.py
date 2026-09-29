from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.freeze_e4_mica_sparse_result import freeze_result


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_SPARSE_RESULT_IMPORT_CONTRACT.json"
)


def _row(index, *, full=-1.0, activity=-1.2, state=-1.1):
    return {
        "deploymentID": f"dep-{index:04d}",
        "full_heldout_log_score": full,
        "activity_knockout_heldout_log_score": activity,
        "state_knockout_heldout_log_score": state,
        "scored_state_context_cells": 10,
    }


def _result(status="E4_SPARSE_EMPIRICAL_RESULT"):
    rows = [_row(i) for i in range(733)]
    return {
        "schema_version": 1,
        "result_id": "e4-mica-exact-sparse-result-v1",
        "programme_id": "E4_MICA_SPARSE_NUTS",
        "endpoint_id": "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION",
        "fit_contract_id": "e4-mica-exact-sparse-fit-v1",
        "status": status,
        "qualification": {
            "workflow_run_id": 36621160011,
            "artifact_id": 11058179352,
            "result_sha256": (
                "2a8ce70ce8eefbbd70a2cdeaa2f4fc558aa64ab061985c263c8d1656979d83ff"
            ),
            "fixture_fingerprint_sha256": (
                "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
            ),
        },
        "fixture_fingerprint_sha256": (
            "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
        ),
        "compaction": {
            "training": {
                "dense_context_count": 615020,
                "compact_context_count": 11531,
                "retained_keys_sha256": (
                    "41bd70aa1f913bcb1c988f6c5cdae3441ed978d4ee0f6791bcfc497290710646"
                ),
            },
            "heldout": {
                "dense_context_count": 560012,
                "compact_context_count": 10168,
                "retained_keys_sha256": (
                    "0ed3fb9e96b1323a4290b7cb92621d219e317b8b916201a1b2665db4a272b1d9"
                ),
            },
        },
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
            "e3_rescue": False,
            "causal_claim_authorized": False,
            "parameter_recovery_claim_authorized": False,
            "same_programme_rerun_allowed": False,
            "post_outcome_retuning_allowed": False,
        },
    }


def _write(tmp_path, payload):
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_import_contract_binds_single_authorized_e4_run():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    execution = value["authorized_execution"]

    assert value["status"] == "FROZEN_PRE_RESULT_IMPORT"
    assert execution["workflow_run_id"] == 36622802225
    assert execution["run_attempt"] == 1
    assert execution["authorization_head_sha"] == (
        "8a1bd87733637494c89e03e389faf6b1c64605a0"
    )
    assert value["import_rule"]["failed_negative_or_timeout_result_must_be_frozen"]
    assert value["import_rule"]["backend_switch_within_e4_allowed"] is False


def test_valid_empirical_result_freezes(tmp_path):
    path = _write(tmp_path, _result())
    receipt = freeze_result(
        path,
        workflow_conclusion="success",
        artifact_id=123,
        artifact_name="e4-mica-sparse-result-36622802225",
        artifact_digest="sha256:abc",
    )

    assert receipt["status"] == "E4_SPARSE_EMPIRICAL_RESULT"
    assert receipt["summary"]["heldout_row_count"] == 733
    assert receipt["summary"]["divergences"]["total"] == 0
    assert receipt["summary"]["scores"]["activity_gain"] == pytest.approx(0.2)
    assert receipt["terminal_rule"]["same_programme_rerun_allowed"] is False


def test_negative_gain_is_frozen_not_retuned(tmp_path):
    payload = _result()
    payload["scores"]["activity_knockout_heldout_log_score"] = -0.8
    payload["scores"]["activity_gain"] = -0.2
    for row in payload["heldout_deployment_scores"]:
        row["activity_knockout_heldout_log_score"] = -0.8
    payload["decision"]["activity_predictive_support_descriptive"] = False
    path = _write(tmp_path, payload)

    receipt = freeze_result(
        path,
        workflow_conclusion="success",
        artifact_id=123,
        artifact_name="result",
        artifact_digest="sha256:abc",
    )
    assert receipt["summary"]["scores"]["activity_gain"] == pytest.approx(-0.2)
    assert receipt["terminal_rule"]["backend_switch_within_e4_allowed"] is False


def test_external_timeout_prewrite_is_importable_only_with_non_success_conclusion(
    tmp_path,
):
    payload = _result()
    for field in (
        "fixture_fingerprint_sha256",
        "compaction",
        "scores",
        "divergences",
        "heldout_deployment_scores",
        "odsp_serialization",
    ):
        payload.pop(field, None)
    payload["status"] = "E4_SPARSE_EXECUTION_STARTED"
    payload["decision"]["sampling_gate_passed"] = None
    path = _write(tmp_path, payload)

    receipt = freeze_result(
        path,
        workflow_conclusion="cancelled",
        artifact_id=123,
        artifact_name="result",
        artifact_digest="sha256:abc",
    )
    assert receipt["status"] == "E4_SPARSE_EXECUTION_STARTED"
    assert receipt["summary"] is None

    with pytest.raises(ValueError, match="incompatible"):
        freeze_result(
            path,
            workflow_conclusion="success",
            artifact_id=123,
            artifact_name="result",
            artifact_digest="sha256:abc",
        )


def test_duplicate_heldout_deployment_fails_closed(tmp_path):
    payload = _result()
    payload["heldout_deployment_scores"][1]["deploymentID"] = "dep-0000"
    path = _write(tmp_path, payload)

    with pytest.raises(ValueError, match="unique non-empty"):
        freeze_result(
            path,
            workflow_conclusion="success",
            artifact_id=123,
            artifact_name="result",
            artifact_digest="sha256:abc",
        )
