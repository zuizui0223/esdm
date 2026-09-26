from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "empirical" / "SNAPSHOT_USA_2024_TRANSPORT_V2_RESULT.json"


def _read():
    return json.loads(RESULT.read_text(encoding="utf-8"))


def test_transport_v2_result_is_frozen_pre_response_rejection():
    result = _read()

    assert result["terminal_status"] == "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY"
    assert result["workflow_run_id"] == 36240304960
    assert result["artifact"]["id"] == 10905890027
    assert result["artifact"]["result_sha256"] == (
        "9a899225c4ed2f07eb865aff3c06c129985172830d86d16de352dd7f23f56e60"
    )
    assert result["frozen_response_boundary"] == {
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }


def test_transport_v2_rejection_is_transport_only_not_scientific():
    result = _read()
    boundary = result["scientific_boundary"]

    assert "deployment file missing required columns" in result["rejection"]["qualification_error"]
    assert result["transport_trace"]["landing_status"] == 200
    assert result["transport_trace"]["deployment_status"] == 200
    assert result["transport_trace"]["sequence_status"] is None
    assert boundary["candidate_consumes_empirical_response_opening"] is False
    assert boundary["changes_r5b_model"] is False
    assert boundary["changes_state_definition"] is False
    assert boundary["changes_holdout_rule"] is False
    assert boundary["changes_stream_partition"] is False
    assert boundary["changes_daymet_contract"] is False
    assert boundary["may_try_new_transport_route"] is True
