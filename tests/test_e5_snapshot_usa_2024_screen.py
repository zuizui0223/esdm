from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs" / "replication" / "E5_CANDIDATE_SNAPSHOT_USA_2024_SCREEN.json"


def _read():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_snapshot_usa_2024_screen_is_response_blind():
    value = _read()
    boundary = value["response_boundary"]
    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert boundary["focal_response_opened"] is False
    assert boundary["sequence_rows_inspected"] is False
    assert boundary["focal_taxon_counts_inspected"] is False
    assert boundary["predictive_scores_inspected"] is False


def test_snapshot_usa_2024_has_strong_detection_calibration_but_fails_temporal_gate():
    value = _read()
    metadata = value["response_blind_metadata"]
    calibration = metadata["detection_calibration"]
    assert metadata["camera_arrays"] == 184
    assert metadata["physical_locations_reported"] == 2715
    assert metadata["deployment_id_row_difference"] == 3
    assert metadata["deployment_identity_uniqueness_verified"] is False
    assert calibration["calibrated_arrays"] == 73
    assert calibration["calibrated_locations"] == 918
    assert metadata["survey_period"]["distinct_calendar_months"] == 5

    gates = {row["gate"]: row for row in value["gates"]}
    assert gates["G1_INDEPENDENT_SOURCE"]["status"] == "PASS"
    assert gates["G2_SCHEMA_EFFORT_TIME"]["status"] == "PARTIAL_SCHEMA_DECLARED_VALUES_UNVERIFIED"
    assert gates["G4_DETECTION_IDENTIFIABILITY"]["status"] == "PROMISING_PENDING_LINKAGE"
    assert gates["G6_TEMPORAL_SUPPORT"]["status"] == "FAIL"
    assert gates["G7_MODEL_FREEZE"]["status"] == "NOT_REACHED"


def test_snapshot_usa_2024_fail_closed_without_threshold_relaxation():
    decision = _read()["decision"]
    assert decision["candidate_qualified"] is False
    assert decision["hard_stop_gate"] == "G6_TEMPORAL_SUPPORT"
    assert decision["failure_is_scientific_negative_result"] is False
    assert decision["focal_response_may_be_opened_for_E5"] is False
    assert decision["model_fit_may_run"] is False
    assert decision["same_candidate_may_be_repaired_using_focal_response"] is False
    assert decision["broader_independent_candidate_search_allowed"] is True
