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
    assert b["emof_rows_read_in_terminal_diagnostic"] == 0
    assert b["occurrence_rows_read"] == 0
    assert b["species_or_taxon_values_read"] == 0
    assert b["eventremarks_values_decoded"] == 0
    assert b["response_dependent_effort_inference_used"] is False


def test_qld_terminal_stop_is_complete_deployment_effort_failure():
    value = _read(SCREEN)
    diag = value["terminal_diagnostic"]
    gates = {row["gate"]: row for row in value["gates"]}

    assert diag["deployment_rows"] == 271
    assert diag["deployment_rows_with_eventDate"] == 0
    assert diag["deployment_rows_missing_eventDate"] == 271
    assert diag["complete_case_deployment_rows"] == 0
    assert gates["G2_SCHEMA_EFFORT_TIME"]["status"] == "FAIL"
    assert gates["G6_TEMPORAL_SUPPORT"]["status"] == "FAIL_ON_DEPLOYMENT_EFFORT"
    assert gates["G7_MODEL_FREEZE"]["status"] == "NOT_REACHED"


def test_qld_terminal_stop_does_not_promote_promising_design_metadata():
    value = _read(SCREEN)
    gates = {row["gate"]: row for row in value["gates"]}
    decision = value["decision"]

    assert gates["G3_CROSSED_DOMAIN"]["status"] == (
        "NOT_ADJUDICATED_AFTER_G2_HARD_STOP"
    )
    assert gates["G4_DETECTION_IDENTIFIABILITY"]["status"] == (
        "NOT_ADJUDICATED_AFTER_G2_HARD_STOP"
    )
    assert decision["candidate_qualified"] is False
    assert decision["focal_response_opening_authorized"] is False
    assert decision["model_fitting_authorized"] is False
    assert decision["same_candidate_repair_from_detection_or_trigger_events_authorized"] is False
    assert decision["same_candidate_threshold_relaxation_authorized"] is False


def test_qld_terminal_provenance_is_pinned():
    value = _read(SCREEN)["terminal_diagnostic"]

    assert value["workflow_run_id"] == 37209976816
    assert value["authorization_sha"] == (
        "bae33cf0ad02f26e60b523e188aec541f24abbef"
    )
    assert value["artifact_id"] == 11306560624
    assert value["artifact_digest"] == (
        "sha256:95119af1abf6916ed6868cc1b4e64edff9f74614b21f685b448b3f68792abd47"
    )
    assert value["result_json_sha256"] == (
        "7970889e49aee7ef77000b1a13a8a7066885a98c4bd77c01db6ea93a44d523ab"
    )


def test_registry_marks_qld_terminal_without_opening_response():
    value = _read(REGISTRY)
    qld = next(
        row for row in value["candidates"]
        if row["candidate_id"] == "qld_wet_tropics_camtrapdp_2022_2023"
    )

    assert qld["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert qld["gates"]["G2_SCHEMA_EFFORT_TIME"] == "FAIL"
    assert qld["gates"]["G6_TEMPORAL_SUPPORT"] == "FAIL_ON_DEPLOYMENT_EFFORT"
    assert qld["response_may_be_opened_for_E5"] is False
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["response_opening_authorized"] is False
