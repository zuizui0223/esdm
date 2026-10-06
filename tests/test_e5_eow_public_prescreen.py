from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "docs" / "replication" / "E5_CANDIDATE_EOW_PUBLIC_PRESCREEN.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_eow_has_g4_first_design_but_remains_pre_response():
    value = _read(SCREEN)
    assert value["status"] == "E5_RESPONSE_BLIND_PUBLIC_PRESCREEN"
    assert value["g4_first_entry"]["D1_DETECTION_IDENTITY"].startswith("PASS_DESIGN_PRINCIPLE")
    assert value["g4_first_entry"]["D2_GEOGRAPHIC_OVERLAP"].startswith("PASS_DESIGN_PRINCIPLE")
    assert value["gates"]["G2_SCHEMA_EFFORT_TIME"].startswith("BLOCKED_")
    assert value["gates"]["G4_DETECTION_IDENTIFIABILITY"].startswith("PASS_DESIGN_PRINCIPLE")
    assert value["decision"] == "E5_CANDIDATE_NOT_YET_QUALIFIED"
    assert value["response_may_be_opened_for_E5"] is False
    assert value["response_boundary"]["focal_event_rows_opened"] == 0
    assert value["response_boundary"]["model_fitting_authorized"] is False


def test_registry_promotes_eow_only_as_design_level_candidate():
    value = _read(REGISTRY)
    row = next(
        x for x in value["candidates"]
        if x["candidate_id"] == "eow_europe_multisite_photogrammetry"
    )
    assert value["current_conclusion"]["screened_candidate_count"] == 15
    assert value["current_conclusion"]["qualified_candidate_count"] == 0
    assert value["current_conclusion"]["strongest_current_named_candidate"] == (
        "eow_europe_multisite_photogrammetry"
    )
    assert row["gates"]["G2_SCHEMA_EFFORT_TIME"].startswith("BLOCKED_")
    assert row["response_may_be_opened_for_E5"] is False
