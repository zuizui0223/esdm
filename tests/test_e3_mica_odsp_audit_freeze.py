from __future__ import annotations

from pathlib import Path

import pytest

from scripts.freeze_e3_mica_odsp_audit_result import freeze_audit


def _boundary():
    return {
        "parallel_not_ordered": True,
        "combined_three_level_filtration_authorized": False,
        "odsp_lattice_authorized": False,
        "population_superpopulation_interpretation_authorized": False,
        "n3_transfer_value_handoff_authorized": False,
        "e2_rescue": False,
        "confirmatory_replication": False,
        "causal_activity": False,
        "causal_state": False,
    }


def _audit():
    return {
        "schema_version": 1,
        "audit_id": "e3-mica-odsp-parallel-audit-result-v1",
        "source": {
            "programme_id": "E3_MICA_EXP",
            "result_id": "e3-mica-reduced-frozen-result-v1",
            "status": "E3_EXPLORATORY_RESULT",
            "workflow_run_id": 123,
            "artifact_id": 456,
            "result_json_sha256": "a" * 64,
        },
        "activity": {
            "endpoint_id": "esdm_e3_mica_activity_transfer_v1",
            "lower_level": "suitability_state",
            "upper_level": "suitability_state_activity",
            "point_mean_gain": 0.10,
            "certified_category": "robust_generalizing",
            "certified_group_status": "robust_positive",
            "certified_lower_bound": 0.02,
            "certified_upper_bound": 0.18,
            "certified_transfer_ceiling": "suitability_state_activity",
            "point_transfer_ceiling": "suitability_state_activity",
            "row_count": 733,
            "block_count": 733,
            "population_result_serialized": True,
            "population_result_scientific_use_authorized": False,
        },
        "state": {
            "endpoint_id": "esdm_e3_mica_state_transfer_v1",
            "lower_level": "suitability_activity",
            "upper_level": "suitability_activity_state",
            "point_mean_gain": -0.03,
            "certified_category": "uncertain",
            "certified_group_status": "uncertain",
            "certified_lower_bound": -0.08,
            "certified_upper_bound": 0.02,
            "certified_transfer_ceiling": "suitability_activity",
            "point_transfer_ceiling": "suitability_activity",
            "row_count": 733,
            "block_count": 733,
            "population_result_serialized": True,
            "population_result_scientific_use_authorized": False,
        },
        "boundary": _boundary(),
    }


def test_freeze_e3_odsp_audit_preserves_parallel_result(tmp_path: Path):
    path = tmp_path / "audit.json"
    import json
    path.write_text(json.dumps(_audit()), encoding="utf-8")

    receipt = freeze_audit(
        path,
        workflow_run_id=999,
        head_sha="b" * 40,
        artifact_id=777,
        artifact_name="e3-mica-odsp-postresult-audit-v1",
        artifact_digest="sha256:" + "c" * 64,
    )

    assert receipt["status"] == "ODSP_AUDIT_COMPLETE"
    assert receipt["parallel_result"]["activity"]["certified_category"] == (
        "robust_generalizing"
    )
    assert receipt["parallel_result"]["state"]["certified_category"] == "uncertain"
    assert receipt["boundary"]["activity_state_parallel_not_ordered"] is True
    assert receipt["boundary"]["n3_transfer_value_handoff_authorized"] is False


def test_freeze_e3_odsp_audit_accepts_terminal_blocked_result(tmp_path: Path):
    import json

    path = tmp_path / "audit.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "audit_id": "e3-mica-odsp-parallel-audit-result-v1",
                "audit_status": "NOT_AUTHORIZED_SOURCE_RESULT",
                "source_status": "E3_EXPLORATORY_SAMPLING_STOP",
                "sampling_gate_passed": False,
                "odsp_executed": False,
                "boundary": _boundary(),
            }
        ),
        encoding="utf-8",
    )
    receipt = freeze_audit(
        path,
        workflow_run_id=999,
        head_sha="b" * 40,
        artifact_id=777,
        artifact_name="e3-mica-odsp-postresult-audit-v1",
        artifact_digest="sha256:" + "c" * 64,
    )

    assert receipt["status"] == "ODSP_AUDIT_NOT_AUTHORIZED"
    assert receipt["parallel_result"] is None
    assert receipt["source_status"] == "E3_EXPLORATORY_SAMPLING_STOP"


def test_freeze_e3_odsp_audit_rejects_population_promotion(tmp_path: Path):
    import json

    audit = _audit()
    audit["boundary"]["n3_transfer_value_handoff_authorized"] = True
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(audit), encoding="utf-8")

    with pytest.raises(ValueError, match="n3_transfer_value_handoff_authorized"):
        freeze_audit(
            path,
            workflow_run_id=999,
            head_sha="b" * 40,
            artifact_id=777,
            artifact_name="e3-mica-odsp-postresult-audit-v1",
            artifact_digest="sha256:" + "c" * 64,
        )


def test_freeze_e3_odsp_audit_rejects_wrong_block_count(tmp_path: Path):
    import json

    audit = _audit()
    audit["activity"]["block_count"] = 732
    path = tmp_path / "audit.json"
    path.write_text(json.dumps(audit), encoding="utf-8")

    with pytest.raises(ValueError, match="block_count must be 733"):
        freeze_audit(
            path,
            workflow_run_id=999,
            head_sha="b" * 40,
            artifact_id=777,
            artifact_name="e3-mica-odsp-postresult-audit-v1",
            artifact_digest="sha256:" + "c" * 64,
        )
