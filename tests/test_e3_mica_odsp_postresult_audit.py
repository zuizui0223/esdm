from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.summarize_e3_mica_odsp_audit import summarize


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E3_MICA_ODSP_POSTRESULT_AUDIT_CONTRACT.json"


def _source(status="E3_EXPLORATORY_RESULT", sampling=True):
    return {
        "schema_version": 1,
        "programme_id": "E3_MICA_EXP",
        "result_id": "e3-mica-reduced-frozen-result-v1",
        "status": status,
        "execution": {
            "workflow_run_id": 123,
            "artifact_id": 456,
            "result_json_sha256": "a" * 64,
        },
        "decision": {"sampling_gate_passed": sampling},
    }


def _receipt(endpoint, lower, upper, gain, lo, hi, category="robust_generalizing", status="robust_positive"):
    return {
        "endpoint_id": endpoint,
        "certified_result": {
            "certification": {
                "point_transfer_ceiling": upper,
                "certified_transfer_ceiling": upper if category == "robust_generalizing" else lower,
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


def test_e3_postresult_contract_forbids_population_and_ordering_claims():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["status"] == "FROZEN_BEFORE_E3_RESULT_IMPORT"
    assert contract["source"]["required_heldout_row_count"] == 733
    assert contract["row_semantics"]["independent_group_count"] == 1
    assert contract["row_semantics"]["expected_block_count"] == 733
    assert contract["row_semantics"]["population_superpopulation_authorized"] is False
    assert contract["audit_outputs"]["n3_transfer_value_handoff_authorized"] is False
    assert contract["ordering_boundary"]["combined_three_level_filtration_authorized"] is False
    assert contract["ordering_boundary"]["odsp_lattice_authorized"] is False


def test_e3_parallel_audit_summary_preserves_two_separate_certifications():
    result = summarize(
        _source(),
        _receipt(
            "esdm_e3_mica_activity_transfer_v1",
            "suitability_state",
            "suitability_state_activity",
            0.11,
            0.02,
            0.20,
        ),
        _receipt(
            "esdm_e3_mica_state_transfer_v1",
            "suitability_activity",
            "suitability_activity_state",
            -0.04,
            -0.10,
            0.03,
            category="uncertain",
            status="uncertain",
        ),
    )

    assert result["activity"]["point_mean_gain"] == pytest.approx(0.11)
    assert result["activity"]["certified_category"] == "robust_generalizing"
    assert result["state"]["point_mean_gain"] == pytest.approx(-0.04)
    assert result["state"]["certified_category"] == "uncertain"
    assert result["activity"]["block_count"] == 733
    assert result["state"]["block_count"] == 733
    assert result["boundary"]["parallel_not_ordered"] is True
    assert result["boundary"]["n3_transfer_value_handoff_authorized"] is False


def test_e3_postresult_audit_rejects_sampling_stop():
    with pytest.raises(ValueError, match="E3_EXPLORATORY_RESULT"):
        summarize(
            _source(status="E3_EXPLORATORY_SAMPLING_STOP", sampling=False),
            _receipt("a", "l", "u", 0.1, 0.0, 0.2),
            _receipt("b", "x", "y", 0.1, 0.0, 0.2),
        )


def test_e3_postresult_audit_rejects_wrong_block_geometry():
    broken = _receipt("a", "l", "u", 0.1, 0.0, 0.2)
    broken["certified_result"]["certification"]["steps"][0]["groups"][0]["block_count"] = 732
    with pytest.raises(ValueError, match="block count drifted"):
        summarize(
            _source(),
            broken,
            _receipt("b", "x", "y", 0.1, 0.0, 0.2),
        )
