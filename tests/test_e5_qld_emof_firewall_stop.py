from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STOP = (
    ROOT / "docs" / "replication" / "E5_QLD_EMOF_TYPES_FIREWALL_STOP.json"
)


def test_consumed_emof_type_run_is_terminal_firewall_stop():
    value = json.loads(STOP.read_text(encoding="utf-8"))
    assert value["status"] == "TERMINAL_RESPONSE_FIREWALL_IMPLEMENTATION_STOP"
    assert value["consumed_route"]["workflow_run_id"] == 37128916426
    assert value["consumed_route"]["authorization_sha"] == (
        "40f759ec4faad9f29ca6c2a4df422fc9ca9ffe61"
    )
    violation = value["implementation_violation"]
    assert "decode" in violation["observed_code_path"][0]
    assert violation["scientific_result_created"] is False


def test_consumed_emof_type_result_cannot_be_adopted_or_rerun():
    value = json.loads(STOP.read_text(encoding="utf-8"))
    governance = value["governance"]
    assert governance["same_route_rerun_allowed"] is False
    assert governance["type_result_adopted"] is False
    assert governance["candidate_status_changed"] is False
    assert governance["corrected_separately_named_value_blind_route_allowed"] is True
    assert governance["focal_response_opening_authorized"] is False
    assert governance["model_fitting_authorized"] is False
