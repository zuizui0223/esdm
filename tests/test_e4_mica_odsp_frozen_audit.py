from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT / "docs" / "replication" / "E4_MICA_ODSP_AUDIT_RESULT_V1.json"
)
RECEIPT = (
    ROOT / "docs" / "replication" / "E4_MICA_ODSP_AUDIT_RECEIPT_V1.json"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_e4_odsp_audit_preserves_point_gain_identity_and_geometry():
    value = _read(AUDIT)

    assert value["audit_status"] == "POSTRESULT_DESCRIPTIVE_AUDIT"
    assert value["activity"]["row_count"] == 733
    assert value["activity"]["block_count"] == 733
    assert value["state"]["row_count"] == 733
    assert value["state"]["block_count"] == 733
    assert value["activity"]["point_gain_identity_passed"] is True
    assert value["state"]["point_gain_identity_passed"] is True
    assert value["activity"]["point_mean_gain"] == pytest.approx(
        -0.6390511804117178
    )
    assert value["state"]["point_mean_gain"] == pytest.approx(
        0.008390925023042506
    )


def test_frozen_e4_odsp_audit_classifies_activity_and_state_without_promotion():
    value = _read(AUDIT)

    assert value["activity"]["certified_category"] == "robust_non_generalizing"
    assert value["activity"]["certified_group_status"] == "robust_nonpositive"
    assert value["activity"]["certified_lower_bound"] == pytest.approx(
        -0.8381153205469307
    )
    assert value["activity"]["certified_upper_bound"] == pytest.approx(
        -0.43998704027650487
    )

    assert value["state"]["certified_category"] == "uncertain"
    assert value["state"]["certified_group_status"] == "uncertain"
    assert value["state"]["certified_lower_bound"] == pytest.approx(
        -0.017381909014266686
    )
    assert value["state"]["certified_upper_bound"] == pytest.approx(
        0.0341637590603517
    )

    assert value["frozen_decision"]["activity_predictive_support_descriptive"] is False
    assert value["frozen_decision"]["state_predictive_support_descriptive"] is True
    assert value["frozen_decision"]["odsp_may_change_decision"] is False


def test_frozen_e4_odsp_audit_forbids_population_lattice_and_causal_use():
    boundary = _read(AUDIT)["boundary"]

    assert boundary["parallel_not_ordered"] is True
    assert boundary["combined_three_level_filtration_authorized"] is False
    assert boundary["odsp_lattice_authorized"] is False
    assert boundary["population_superpopulation_interpretation_authorized"] is False
    assert boundary["n3_transfer_value_handoff_authorized"] is False
    assert boundary["confirmatory_replication"] is False
    assert boundary["causal_activity"] is False
    assert boundary["causal_state"] is False
    assert boundary["e4_rerun_or_retuning_authorized"] is False
    assert boundary["backend_switch_authorized"] is False


def test_e4_odsp_audit_receipt_pins_workflow_artifact_and_odsp_commit():
    value = _read(RECEIPT)

    assert value["status"] == "FROZEN_POSTRESULT_DESCRIPTIVE_AUDIT"
    assert value["source_result"]["workflow_run_id"] == 36622802225
    assert value["source_result"]["artifact_id"] == 11059622869
    assert value["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )

    execution = value["audit_execution"]
    assert execution["workflow_run_id"] == 36651346211
    assert execution["workflow_conclusion"] == "success"
    assert execution["head_sha"] == (
        "9426d7f00444beb02ce6d1ac38445dfb5f060f6e"
    )
    assert execution["artifact_id"] == 11071096409
    assert execution["artifact_digest"] == (
        "sha256:edc19bae37786d03084ffeb08518fec5f2686a8170e29877dd7c1db8720fb269"
    )
    assert execution["audit_json_sha256"] == (
        "d9280377f407b24ff61e11c2eab9e7b53d6293e2b24ce6b3187f36402e70838e"
    )
