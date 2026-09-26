from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "ODSP_TRANSFER_EVIDENCE_LEDGER_RECEIPT_V2.json"


def _read():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_v2_receipt_pins_exact_generated_ledger():
    receipt = _read()
    generation = receipt["generation"]

    assert receipt["implementation_merge_sha"] == (
        "2bef09c65746ef8c5bab8beeb06962263a05d7d2"
    )
    assert generation["source_head_sha"] == (
        "70e6520e30ec29a2afd79b716a4a3816a36c9599"
    )
    assert generation["workflow_run_id"] == 36222395619
    assert generation["artifact_id"] == 10899980400
    assert generation["artifact_digest"] == (
        "sha256:daf6d6c66a0cea3582e26511b501631a4988ee57a5e46ec77126f84c8a0fb2f0"
    )
    assert generation["portfolio_json_sha256"] == (
        "c6a76b7245c5b4dac0edc5b5584232933f3f3594f7fa757e5a6c1c1bef9630d1"
    )
    assert generation["portfolio_fingerprint"] == (
        "5285de0dd8b64a366e957a3ce5610d00e24b8d3a0665878b0ccb17d00360b41d"
    )
    assert generation["canonical_snapshot_in_repository"] is False
    assert generation["deterministic_rebuild_authorized"] is True


def test_v2_receipt_accounts_for_complete_registry_not_only_successes():
    coverage = _read()["coverage"]

    assert coverage["registry_source_count"] == 14
    assert coverage["validated_item_count"] == 4
    assert coverage["excluded_source_count"] == 10
    assert coverage["scientific_fail_count"] == 2
    assert coverage["every_registry_source_accounted_for"] is True
    assert coverage["status_counts"] == {
        "evidence_tier_not_transfer": 1,
        "gain_only_not_exportable": 1,
        "identification_only_not_transfer": 2,
        "non_nested_comparison_not_transfer": 4,
        "scientific_fail_not_exportable": 2,
        "validated_exportable": 4,
    }


def test_v05f_fail_is_explicitly_unsupported_not_zero():
    row = _read()["interaction_fail_sentinel"]

    assert row["source_id"] == "v05f_directed_interaction_replication"
    assert row["registry_status"] == "scientific_fail_not_exportable"
    assert row["frozen_result_status"] == "FAIL"
    assert row["numeric_transfer_value"] is None
    assert row["numeric_transfer_value_authorized"] is False
    assert row["unsupported_not_zero"] is True
    assert row["positive_world"]["positive_gain_rate"] == 1.0
    assert row["positive_world"]["mean_heldout_gain"] == 1.1190587549523654
    assert row["specificity_null"]["material_gain_count"] == 5
    assert row["specificity_null"]["maximum_allowed_count"] == 4
    assert row["failed_check"] == "null_material_gain_rate"


def test_v2_receipt_forbids_selection_bias_ranking_and_action():
    boundary = _read()["boundaries"]

    assert boundary["success_only_display_authorized"] is False
    assert boundary["unsupported_source_equals_zero_transfer"] is False
    assert boundary["scientific_fail_numeric_promotion_authorized"] is False
    assert boundary["gain_only_reconstruction_authorized"] is False
    assert boundary["non_nested_relabelling_authorized"] is False
    assert boundary["cross_programme_numeric_ranking_authorized"] is False
    assert boundary["global_information_ladder_authorized"] is False
    assert boundary["lattice_inference_created"] is False
    assert boundary["eog_consumption_authorized"] is False
    assert boundary["n4_action_authorized"] is False
    assert boundary["n4_survey_action_owner"] == "ACSP"
