from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.summarize_e4_mica_odsp_audit import summarize


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "replication"
    / "E4_MICA_ODSP_POSTRESULT_AUDIT_CONTRACT.json"
)


def _source():
    return {
        "schema_version": 1,
        "programme_id": "E4_MICA_SPARSE_NUTS",
        "result_id": "e4-mica-exact-sparse-frozen-result-v1",
        "status": "E4_SPARSE_EMPIRICAL_RESULT",
        "execution": {
            "workflow_run_id": 36622802225,
            "artifact_id": 11059622869,
            "result_json_sha256": (
                "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2"
            ),
        },
        "decision": {
            "sampling_gate_passed": True,
            "activity_predictive_support_descriptive": False,
            "state_predictive_support_descriptive": True,
        },
        "summary": {
            "scores": {
                "activity_gain": -0.6390511804117178,
                "state_gain": 0.008390925023042506,
            }
        },
    }


def _receipt(endpoint, lower, upper, gain, lo, hi, category, status):
    return {
        "endpoint_id": endpoint,
        "certified_result": {
            "certification": {
                "point_transfer_ceiling": upper,
                "certified_transfer_ceiling": lower,
                "steps": [
                    {
                        "lower_level": lower,
                        "upper_level": upper,
                        "category": category,
                        "groups": [
                            {
                                "group": "MICA_MUSKRAT",
                                "row_count": 733,
                                "block_count": 733,
                                "mean_gain": gain,
                                "lower_bound": lo,
                                "upper_bound": hi,
                                "status": status,
                                "estimable": True,
                            }
                        ],
                    }
                ],
            }
        },
        "population_result": {
            "group_count": 1,
            "familywise_confirmatory_claim": False,
        },
    }


def test_e4_postresult_odsp_contract_forbids_population_and_decision_promotion():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert value["status"] == "POSTRESULT_DESCRIPTIVE_AUDIT_FROZEN"
    assert value["row_semantics"]["independent_group_count"] == 1
    assert value["row_semantics"]["expected_block_count"] == 733
    assert value["row_semantics"]["population_superpopulation_authorized"] is False
    assert value["audit_outputs"]["n3_transfer_value_handoff_authorized"] is False
    assert "changing activity or state support decisions" in value["interpretation"]["forbidden"]


def test_e4_odsp_summary_preserves_frozen_point_signs_and_decisions():
    activity = _receipt(
        "esdm_e4_mica_activity_transfer_v1",
        "suitability_state",
        "suitability_state_activity",
        -0.6390511804117178,
        -0.8,
        -0.4,
        "negative",
        "robust_negative",
    )
    state = _receipt(
        "esdm_e4_mica_state_transfer_v1",
        "suitability_activity",
        "suitability_activity_state",
        0.008390925023042506,
        -0.01,
        0.03,
        "uncertain",
        "uncertain",
    )
    result = summarize(_source(), activity, state)

    assert result["activity"]["point_mean_gain"] == pytest.approx(-0.6390511804117178)
    assert result["state"]["point_mean_gain"] == pytest.approx(0.008390925023042506)
    assert result["frozen_decision"]["activity_predictive_support_descriptive"] is False
    assert result["frozen_decision"]["state_predictive_support_descriptive"] is True
    assert result["frozen_decision"]["odsp_may_change_decision"] is False
    assert result["boundary"]["n3_transfer_value_handoff_authorized"] is False


def test_e4_odsp_summary_fails_if_odsp_point_gain_drifts():
    activity = _receipt(
        "esdm_e4_mica_activity_transfer_v1",
        "a",
        "b",
        -0.60,
        -0.8,
        -0.4,
        "negative",
        "robust_negative",
    )
    state = _receipt(
        "esdm_e4_mica_state_transfer_v1",
        "c",
        "d",
        0.008390925023042506,
        -0.01,
        0.03,
        "uncertain",
        "uncertain",
    )
    with pytest.raises(ValueError, match="point gain drifted"):
        summarize(_source(), activity, state)


def test_e4_odsp_summary_rejects_wrong_block_geometry():
    activity = _receipt(
        "esdm_e4_mica_activity_transfer_v1",
        "a",
        "b",
        -0.6390511804117178,
        -0.8,
        -0.4,
        "negative",
        "robust_negative",
    )
    activity["certified_result"]["certification"]["steps"][0]["groups"][0][
        "block_count"
    ] = 732
    state = _receipt(
        "esdm_e4_mica_state_transfer_v1",
        "c",
        "d",
        0.008390925023042506,
        -0.01,
        0.03,
        "uncertain",
        "uncertain",
    )
    with pytest.raises(ValueError, match="block count drifted"):
        summarize(_source(), activity, state)
