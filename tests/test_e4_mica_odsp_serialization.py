from __future__ import annotations

import json
from pathlib import Path

import pytest

from esdm.transfer import (
    build_e4_mica_activity_odsp_bundle,
    build_e4_mica_state_odsp_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
SERIALIZATION = (
    ROOT / "docs" / "replication" / "E4_MICA_ODSP_SERIALIZATION_CONTRACT.json"
)


def _row(index: int):
    return {
        "deploymentID": f"dep-{index:04d}",
        "full_heldout_log_score": -7.0 - index * 1e-6,
        "activity_knockout_heldout_log_score": -6.5 - index * 1e-6,
        "state_knockout_heldout_log_score": -7.1 - index * 1e-6,
    }


def _result():
    rows = [_row(i) for i in range(733)]
    return {
        "result_id": "e4-mica-exact-sparse-result-v1",
        "programme_id": "E4_MICA_SPARSE_NUTS",
        "endpoint_id": "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION",
        "status": "E4_SPARSE_EMPIRICAL_RESULT",
        "decision": {"sampling_gate_passed": True},
        "response_boundary": {
            "state_calibration_stream_present_in_fit": False,
            "new_external_response_gets": 0,
        },
        "fixture_fingerprint_sha256": (
            "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
        ),
        "compaction": {
            "training": {
                "compact_context_count": 11531,
                "retained_keys_sha256": (
                    "41bd70aa1f913bcb1c988f6c5cdae3441ed978d4ee0f6791bcfc497290710646"
                ),
            },
            "heldout": {
                "compact_context_count": 10168,
                "retained_keys_sha256": (
                    "0ed3fb9e96b1323a4290b7cb92621d219e317b8b916201a1b2665db4a272b1d9"
                ),
            },
        },
        "odsp_serialization": {
            "row_count": 733,
            "absolute_scores_serialized": True,
            "gain_only_serialization": False,
            "same_scored_cells_across_models": True,
        },
        "heldout_deployment_scores": rows,
    }


def test_e4_odsp_serialization_contract_is_parallel_and_nonpopulation():
    value = json.loads(SERIALIZATION.read_text(encoding="utf-8"))

    assert value["required_source_status"] == "E4_SPARSE_EMPIRICAL_RESULT"
    assert value["required_heldout_rows"] == 733
    assert value["row_semantics"]["independent_group_count"] == 1
    assert value["row_semantics"]["block_count"] == 733
    assert value["ordering_boundary"]["natural_order_between_activity_and_state"] is False
    assert value["ordering_boundary"]["combined_three_level_filtration_authorized"] is False
    assert value["inference_boundary"]["superpopulation_interpretation_authorized"] is False
    assert value["inference_boundary"]["n3_transfer_value_handoff_authorized"] is False


def test_e4_activity_bundle_uses_absolute_parallel_scores():
    bundle = build_e4_mica_activity_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_e4_mica_activity_transfer_v1"
    assert bundle.contract["evaluation"]["analysis_mode"] == "descriptive"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_state",
            "information": ["suitability", "state"],
            "score_column": "score__suitability_state",
        },
        {
            "name": "suitability_state_activity",
            "information": ["suitability", "state", "activity"],
            "score_column": "score__suitability_state_activity",
        },
    ]
    assert bundle.contract["columns"]["group"] == "group"
    assert bundle.contract["columns"]["block"] == "block"
    assert bundle.contract["columns"]["population_cluster"] is None
    assert len(bundle.rows) == 733
    assert {row["group"] for row in bundle.rows} == {"MICA_MUSKRAT"}
    assert len({row["block"] for row in bundle.rows}) == 733


def test_e4_state_bundle_uses_absolute_parallel_scores():
    bundle = build_e4_mica_state_odsp_bundle(_result())

    assert bundle.contract["endpoint_id"] == "esdm_e4_mica_state_transfer_v1"
    assert bundle.contract["levels"] == [
        {
            "name": "suitability_activity",
            "information": ["suitability", "activity"],
            "score_column": "score__suitability_activity",
        },
        {
            "name": "suitability_activity_state",
            "information": ["suitability", "activity", "state"],
            "score_column": "score__suitability_activity_state",
        },
    ]
    assert len(bundle.rows) == 733


def test_e4_bundle_fails_closed_on_fixture_or_sparse_geometry_drift():
    value = _result()
    value["fixture_fingerprint_sha256"] = "x" * 64
    with pytest.raises(ValueError, match="fixture fingerprint"):
        build_e4_mica_activity_odsp_bundle(value)

    value = _result()
    value["compaction"]["heldout"]["compact_context_count"] = 10167
    with pytest.raises(ValueError, match="heldout compact context"):
        build_e4_mica_state_odsp_bundle(value)


def test_e4_bundle_fails_closed_on_duplicate_rows_or_gain_only_serialization():
    value = _result()
    value["heldout_deployment_scores"][1]["deploymentID"] = "dep-0000"
    with pytest.raises(ValueError, match="unique non-empty"):
        build_e4_mica_activity_odsp_bundle(value)

    value = _result()
    value["odsp_serialization"]["gain_only_serialization"] = True
    with pytest.raises(ValueError, match="gain-only"):
        build_e4_mica_state_odsp_bundle(value)
