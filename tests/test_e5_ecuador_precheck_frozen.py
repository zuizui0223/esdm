from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "replication" / "E5_ECUADOR_EVENT_CORE_PRECHECK_RESULT.json"
RECEIPT = ROOT / "docs" / "replication" / "E5_ECUADOR_EVENT_CORE_PRECHECK_RECEIPT.json"
ADJ = ROOT / "docs" / "replication" / "E5_CANDIDATE_ECUADOR_RESPONSE_BLIND_ADJUDICATION.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_ecuador_precheck_kept_occurrence_response_closed():
    result = _read(RESULT)
    boundary = result["response_boundary"]
    assert result["status"] == "E5_RESPONSE_BLIND_EVENT_CORE_PRECHECK"
    assert boundary["event_core_opened"] is True
    assert boundary["occurrence_extension_opened"] is False
    assert boundary["occurrence_rows_read"] == 0
    assert result["event_core_geometry"]["physical_location_candidate_count"] == 697


def test_ecuador_precheck_receipt_pins_one_shot_artifact():
    value = _read(RECEIPT)
    execution = value["execution"]
    assert execution["workflow_run_id"] == 36663028218
    assert execution["authorization_sha"] == "d79134bce6c02402eaac3c95d9776f568cff0321"
    assert execution["artifact_id"] == 11074813407
    assert execution["artifact_digest"] == (
        "sha256:a09203e11ed1e530dc0f407b6baeef2fbc64f78b917dcb91c8f70ad7d6c7852c"
    )
    assert execution["result_json_sha256"] == (
        "c84e4feddb2e3c6a3a5e5dcd7c3d317e3f5e1d0e78781db810a8c41c7be982f6"
    )
    assert value["response_boundary"]["occurrence_rows_read"] == 0


def test_ecuador_candidate_stops_on_crossed_domain_without_response_rescue():
    value = _read(ADJ)
    assert value["status"] == "E5_CANDIDATE_NOT_QUALIFIED"
    assert value["gates"]["G3_CROSSED_DOMAIN"] == (
        "FAIL_FROZEN_ACCEPTABLE_CROSSING_NOT_ESTABLISHED"
    )
    assert value["hard_stop"]["gate"] == "G3_CROSSED_DOMAIN"
    assert value["hard_stop"]["event_date_parser_issue_needs_repair_for_this_candidate"] is False
    assert value["decision"]["focal_response_opening_authorized"] is False
    assert value["decision"]["event_date_format_rescue_authorized"] is False
    assert value["decision"]["occurrence_extension_opening_authorized"] is False
    assert value["decision"]["broader_candidate_search_authorized"] is True
