from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_HENRICH10_SCREEN.json"
CONTRACT = ROOT / "docs" / "replication" / "E5_HENRICH10_OSF_MANIFEST_CONTRACT.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_henrich10_public_design_passes_g3_but_keeps_g4_promising():
    value = _read(SCREEN)
    gates = {row["gate"]: row["status"] for row in value["gates"]}
    assert value["status"] == "E5_CANDIDATE_G3_PASS_G4_PROMISING_PENDING_OSF_SCHEMA"
    assert value["public_design"]["geographic_regimes"] == 10
    assert value["public_design"]["physical_camera_traps_total"] == 586
    assert gates["G3_CROSSED_DOMAIN"] == "PASS_DESIGN_PRINCIPLE_PUBLIC_METHODS"
    assert gates["G4_DETECTION_IDENTIFIABILITY"] == (
        "PROMISING_CTDS_RADIAL_DISTANCE_PATH_PENDING_OSF_LINKAGE"
    )
    assert gates["G6_TEMPORAL_SUPPORT"] == "PASS_PUBLIC_DESIGN_ONE_YEAR_PER_GEOGRAPHY"
    assert value["response_boundary"]["focal_event_rows_read"] == 0
    assert value["decision"]["candidate_qualified"] is False
    assert value["decision"]["focal_response_opening_authorized"] is False
    assert value["decision"]["model_fitting_authorized"] is False


def test_henrich10_next_step_is_manifest_only_and_cannot_open_files():
    value = _read(CONTRACT)
    assert value["status"] == "FROZEN_MANIFEST_NOT_AUTHORIZED"
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False
    assert value["decision_boundary"]["child_contract_required_before_any_file_content_read"] is True
    fw = value["response_firewall"]
    assert fw["file_content_read_authorized"] is False
    assert fw["file_download_authorized"] is False
    assert fw["file_preview_authorized"] is False
    assert fw["biological_rows_read_authorized"] is False
    assert fw["focal_response_opening_authorized"] is False


def test_registry_marks_henrich10_terminal_and_tracks_new_priority():
    value = _read(REGISTRY)
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "henrich10_ctds_germany_2019_2020"
    )
    assert value["current_conclusion"]["screened_candidate_count"] == 16
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["strongest_current_named_candidate"] == ("kays41_emammal_team_2020"
    )
    assert row["response_opened"] is False
    assert row["response_may_be_opened_for_E5"] is False
    assert row["decision"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert row["gates"]["G4_DETECTION_IDENTIFIABILITY"] == (
        "FAIL_PUBLIC_REFERENCE_CALIBRATION_PATH_NOT_EXPOSED"
    )
