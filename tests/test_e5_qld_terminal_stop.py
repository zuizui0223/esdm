from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_QLD_TERMINAL_SCREEN.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_qld_terminal_stop_preserves_response_blind_boundary():
    value = _read(SCREEN)
    b = value["response_boundary"]

    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert b["focal_response_opened"] is False
    assert b["biological_event_core_rows_read"] == 0
    assert b["emof_rows_read_in_terminal_effort_diagnostics"] == 0
    assert b["occurrence_rows_read"] == 0
    assert b["species_or_taxon_values_read"] == 0
    assert b["eventremarks_values_decoded"] == 0
    assert b["trigger_eventdates_decoded"] == 0
    assert b["response_dependent_effort_inference_used"] is False


def test_qld_direct_and_parent_effort_paths_both_fail():
    value = _read(SCREEN)
    direct = value["deployment_diagnostic"]
    parent = value["survey_parent_diagnostic"]

    assert direct["deployment_rows"] == 271
    assert direct["deployment_rows_missing_eventDate"] == 271
    assert direct["complete_case_deployment_rows"] == 0

    assert parent["survey_rows"] == 6
    assert parent["survey_rows_missing_eventDate"] == 6
    assert parent["deployment_rows"] == 271
    assert parent["unique_deployment_to_survey_matches"] == 271
    assert parent["deployments_with_valid_inherited_interval"] == 0
    assert parent["trigger_rows_skipped_without_eventdate_decode"] == 33522


def test_qld_terminal_gate_boundary_is_fail_closed():
    value = _read(SCREEN)
    gates = {row["gate"]: row for row in value["gates"]}
    decision = value["decision"]

    assert gates["G2_SCHEMA_EFFORT_TIME"]["status"] == "FAIL"
    assert gates["G6_TEMPORAL_SUPPORT"]["status"] == "FAIL_ON_DEPLOYMENT_EFFORT"
    assert gates["G3_CROSSED_DOMAIN"]["status"] == "NOT_ADJUDICATED_AFTER_G2_HARD_STOP"
    assert gates["G4_DETECTION_IDENTIFIABILITY"]["status"] == "NOT_ADJUDICATED_AFTER_G2_HARD_STOP"
    assert gates["G7_MODEL_FREEZE"]["status"] == "NOT_REACHED"

    assert decision["candidate_qualified"] is False
    assert decision["focal_response_opening_authorized"] is False
    assert decision["model_fitting_authorized"] is False
    assert decision["infer_effort_from_trigger_or_detection_events_authorized"] is False
    assert decision["decode_trigger_eventdates_to_repair_candidate_authorized"] is False
    assert decision["threshold_relaxation_authorized"] is False


def test_qld_terminal_provenance_pins_both_one_shots():
    value = _read(SCREEN)

    direct = value["deployment_diagnostic"]
    assert direct["workflow_run_id"] == 37209976816
    assert direct["authorization_sha"] == "bae33cf0ad02f26e60b523e188aec541f24abbef"
    assert direct["artifact_id"] == 11306560624
    assert direct["result_json_sha256"] == (
        "7970889e49aee7ef77000b1a13a8a7066885a98c4bd77c01db6ea93a44d523ab"
    )

    parent = value["survey_parent_diagnostic"]
    assert parent["workflow_run_id"] == 37210779558
    assert parent["authorization_sha"] == "6fc14000e042313357cfe8080aba5054e1eaa194"
    assert parent["artifact_id"] == 11306008942
    assert parent["result_json_sha256"] == (
        "21daae422d44f6dca802aace438d2a5734981e47d4d3e254b032e2e063655f88"
    )


def test_registry_marks_qld_terminal_and_keeps_e5_closed():
    value = _read(REGISTRY)
    qld = next(
        row for row in value["candidates"]
        if row["candidate_id"] == "qld_wet_tropics_camtrapdp_2022_2023"
    )

    assert qld["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert qld["gates"]["G2_SCHEMA_EFFORT_TIME"] == "FAIL"
    assert qld["gates"]["G6_TEMPORAL_SUPPORT"] == "FAIL_ON_DEPLOYMENT_EFFORT"
    assert qld["response_may_be_opened_for_E5"] is False

    current = value["current_conclusion"]
    assert current["qualified_candidate_count"] == 0
    assert current["response_opening_authorized"] is False
    assert current["model_fitting_authorized"] is False
