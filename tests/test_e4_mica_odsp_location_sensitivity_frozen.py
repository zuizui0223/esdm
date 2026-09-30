from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RESULT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_ODSP_LOCATION_BLOCK_SENSITIVITY_RESULT.json"
)
RECEIPT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_ODSP_LOCATION_BLOCK_SENSITIVITY_RECEIPT.json"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_location_block_result_preserves_frozen_point_gains():
    value = _read(RESULT)

    assert value["status"] == "POSTRESULT_DESCRIPTIVE_SENSITIVITY"
    assert value["activity"]["row_count"] == 733
    assert value["activity"]["physical_location_block_count"] == 27
    assert value["activity"]["point_gain_identity_passed"] is True
    assert value["activity"]["point_mean_gain"] == pytest.approx(
        -0.6390511804117178
    )
    assert value["state"]["row_count"] == 733
    assert value["state"]["physical_location_block_count"] == 27
    assert value["state"]["point_gain_identity_passed"] is True
    assert value["state"]["point_mean_gain"] == pytest.approx(
        0.008390925023042506
    )


def test_location_block_activity_non_generalization_survives_clustering():
    value = _read(RESULT)

    activity = value["activity"]
    assert activity["certified_category"] == "robust_non_generalizing"
    assert activity["certified_group_status"] == "robust_nonpositive"
    assert activity["certified_lower_bound"] == pytest.approx(
        -1.2594059939334707
    )
    assert activity["certified_upper_bound"] == pytest.approx(
        -0.01869636688996479
    )
    assert activity["certified_upper_bound"] < 0.0

    state = value["state"]
    assert state["certified_category"] == "uncertain"
    assert state["certified_group_status"] == "uncertain"
    assert state["certified_lower_bound"] < 0.0 < state["certified_upper_bound"]


def test_location_block_sensitivity_does_not_promote_population_claims():
    boundary = _read(RESULT)["boundary"]

    assert boundary["official_733_deployment_block_audit_replaced"] is False
    assert boundary["frozen_e4_decision_changed"] is False
    assert boundary["superpopulation_interpretation_authorized"] is False
    assert boundary["n3_handoff_authorized"] is False
    assert boundary["confirmatory_claim"] is False
    assert boundary["causal_claim"] is False


def test_location_block_receipt_pins_artifact_and_odsp_commit():
    value = _read(RECEIPT)

    assert value["status"] == "FROZEN_POSTRESULT_DESCRIPTIVE_SENSITIVITY"
    assert value["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )
    execution = value["execution"]
    assert execution["workflow_run_id"] == 36657049712
    assert execution["head_sha"] == (
        "8784dda128b9e6708c8dac38f3ca28eb1a043776"
    )
    assert execution["artifact_id"] == 11072487492
    assert execution["artifact_digest"] == (
        "sha256:42814eb7b970f2fd3a3f26c57afff717602abb83ad7b807727c56129d451869f"
    )
    assert execution["result_json_sha256"] == (
        "d5363cc1111a8e1979c6cd01fce08ea49955dd73095b98a518d16d19dea9744d"
    )
