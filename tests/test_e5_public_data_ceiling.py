from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CEILING = ROOT / "docs" / "replication" / "E5_PUBLIC_DATA_CEILING.json"
REGISTRY = ROOT / "docs" / "replication" / "E5_RESPONSE_BLIND_CANDIDATE_REGISTRY.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_e5_public_data_ceiling_closes_generic_candidate_search():
    value = _read(CEILING)
    assert value["status"] == "FROZEN_PUBLIC_DATA_CEILING"
    assert value["evidence"]["screened_candidates"] == 15
    assert value["evidence"]["qualified_candidates"] == 0
    assert value["evidence"]["focal_response_opened_for_candidate_selection"] is False
    stop = value["search_stop_rule"]
    assert stop["generic_candidate_discovery_authorized"] is False
    assert stop["candidate_count_may_increment_under_current_programme"] is False
    assert stop["stopped_candidate_repair_using_response_authorized"] is False
    assert stop["same_candidate_transport_or_schema_retry_authorized"] is False
    assert stop["reopening_requires_new_frozen_child_contract"] is True


def test_e5_ceiling_preserves_e4_and_authorizes_no_response_or_fit():
    value = _read(CEILING)
    decision = value["decision"]
    assert decision["candidate_search_closed"] is True
    assert decision["focal_response_opening_authorized"] is False
    assert decision["model_fitting_authorized"] is False
    assert decision["E4_remains_terminal_empirical_endpoint"] is True
    assert decision["E5_negative_biological_claim_authorized"] is False
    assert decision["future_different_estimand_route_must_be_separately_named"] is True


def test_registry_is_frozen_at_fifteen_zero_qualified():
    value = _read(REGISTRY)
    current = value["current_conclusion"]
    assert value["status"] == "RESPONSE_BLIND_SEARCH_CEILING_FROZEN"
    assert current["screened_candidate_count"] == 15
    assert current["qualified_candidate_count"] == 0
    assert current["candidate_search_active"] is False
    assert current["generic_candidate_discovery_authorized"] is False
    assert current["response_opening_authorized"] is False
    assert current["model_fitting_authorized"] is False
    assert current["strongest_current_named_candidate"] == "kays41_emammal_team_2020"
    assert all(
        row.get("response_may_be_opened_for_E5") is False
        for row in value["candidates"]
    )
