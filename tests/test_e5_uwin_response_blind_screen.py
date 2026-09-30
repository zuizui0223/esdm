from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_UWIN_SCREEN.json"
RECEIPT = ROOT / "docs" / "replication" / "E5_UWIN_ZENODO_INVENTORY_RECEIPT.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_uwin_inventory_receipt_preserves_response_firewall():
    value = _read(RECEIPT)
    assert value["status"] == "FROZEN_RESPONSE_BLIND_PACKAGE_INVENTORY"
    assert value["source_identity"]["observed_archive_md5"] == (
        "72c6e7d51f359e84e2e49154942b4c98"
    )
    assert value["execution"]["workflow_run_id"] == 36667619946
    assert value["execution"]["artifact_id"] == 11076861763
    assert value["execution"]["inventory_json_sha256"] == (
        "78edcb026efd583b073aa62c3277e2f5c4931b9c66f6fe8746eef3d0f89c8aad"
    )
    assert value["response_boundary"]["data_rows_read"] == 0
    assert value["response_boundary"]["response_rows_read"] == 0
    assert value["response_boundary"]["focal_response_opened"] is False


def test_uwin_screen_fails_crossed_domain_and_detection_identifiability():
    value = _read(SCREEN)
    gates = {row["gate"]: row for row in value["gates"]}
    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert gates["G1_INDEPENDENT_SOURCE"]["status"] == "PASS"
    assert gates["G2_SCHEMA_EFFORT_TIME"]["status"] == "PARTIAL_NOT_FULL_PASS"
    assert gates["G3_CROSSED_DOMAIN"]["status"] == "FAIL"
    assert gates["G4_DETECTION_IDENTIFIABILITY"]["status"] == "FAIL"
    assert gates["G5_PHYSICAL_REPLICATION"]["status"] == "CAPACITY_PASS_SPLIT_NOT_FROZEN"
    assert gates["G7_MODEL_FREEZE"]["status"] == "NOT_REACHED"


def test_uwin_screen_does_not_open_response_or_authorize_fit():
    value = _read(SCREEN)
    boundary = value["response_boundary"]
    decision = value["decision"]
    assert boundary["focal_response_opened"] is False
    assert boundary["data_rows_opened"] == 0
    assert boundary["species_detection_rows_opened"] == 0
    assert decision["candidate_qualified"] is False
    assert decision["hard_stop_gates"] == [
        "G3_CROSSED_DOMAIN",
        "G4_DETECTION_IDENTIFIABILITY",
    ]
    assert decision["focal_response_opening_authorized"] is False
    assert decision["model_fitting_authorized"] is False


def test_uwin_may_not_be_relabelled_as_e5_test():
    value = _read(SCREEN)["reuse_boundary"]
    assert value["may_be_useful_for_separate_diel_nonstationarity_research"] is True
    assert value["may_be_relabelled_as_E5_activity_detection_test"] is False
