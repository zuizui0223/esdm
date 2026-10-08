from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs" / "replication" / "E5_HENRICH10_OSF_MANIFEST_RECEIPT.json"
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_HENRICH10_TERMINAL_SCREEN.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_henrich10_manifest_receipt_pins_successful_response_blind_run():
    value = _read(RECEIPT)
    execution = value["execution"]
    boundary = value["response_boundary"]

    assert value["status"] == "FROZEN_RESPONSE_BLIND_OSF_MANIFEST_RESULT"
    assert execution["workflow_run_id"] == 37482147928
    assert execution["authorization_sha"] == "02bfea1968709cc682b53ddef2cc6b25d9a6b2a5"
    assert execution["artifact_id"] == 11426981455
    assert execution["artifact_digest"] == (
        "sha256:73a98895a9ed936e29f522b7a94a4a4f046ddabcce45176ced30ff64bd6136cb"
    )
    assert execution["result_json_sha256"] == (
        "1cd15f3b70fd849a513fd3920167c09809d5898b783b108795460bff528d2ad8"
    )
    assert boundary["file_downloads_followed"] == 0
    assert boundary["file_previews_opened"] == 0
    assert boundary["file_contents_opened"] == 0
    assert boundary["biological_rows_read"] == 0
    assert boundary["focal_response_opened"] is False


def test_henrich10_manifest_has_effort_and_distance_outputs_but_no_reference_calibration_route():
    value = _read(RECEIPT)
    names = value["manual_name_path_adjudication"]
    summary = value["manifest_summary"]

    assert summary["entry_count"] == 29
    assert summary["file_count"] == 27
    assert summary["samplingdays_files"] == 10
    assert summary["distances_export_files"] == 10
    assert summary["distance_sampling_scripts"] == 2
    assert names["effort_route_visible"] is True
    assert names["ctds_radial_distance_route_visible"] is True
    assert names["independently_named_reference_calibration_route_visible"] is False
    assert names["child_contract_allowed_under_frozen_three_route_rule"] is False
    assert value["implementation_note"]["same_one_shot_rerun_allowed"] is False


def test_henrich10_terminal_screen_stops_at_g4_without_opening_response():
    value = _read(SCREEN)
    gates = {row["gate"]: row["status"] for row in value["gates"]}

    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert value["hard_stop"]["gate"] == "G4_DETECTION_IDENTIFIABILITY"
    assert gates["G3_CROSSED_DOMAIN"] == "PASS_DESIGN_PRINCIPLE_PUBLIC_METHODS"
    assert gates["G4_DETECTION_IDENTIFIABILITY"] == (
        "FAIL_PUBLIC_REFERENCE_CALIBRATION_PATH_NOT_EXPOSED"
    )
    assert value["response_boundary"]["file_contents_opened"] == 0
    assert value["response_boundary"]["biological_rows_read"] == 0
    assert value["decision"]["candidate_qualified"] is False
    assert value["decision"]["focal_response_opening_authorized"] is False
    assert value["decision"]["model_fitting_authorized"] is False
    assert value["decision"]["same_manifest_authorization_may_be_rerun"] is False


def test_registry_freezes_henrich10_terminal_and_keeps_zero_qualified():
    value = _read(REGISTRY)
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "henrich10_ctds_germany_2019_2020"
    )

    assert value["current_conclusion"]["screened_candidate_count"] == 16
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["strongest_current_named_candidate"] == ("kays41_emammal_team_2020"
    )
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"] == (
        "FAIL_PUBLIC_REFERENCE_CALIBRATION_PATH_NOT_EXPOSED"
    )
    assert row["response_may_be_opened_for_E5"] is False
