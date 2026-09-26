import json
from pathlib import Path


def test_snapshot_japan_geometry_contract_is_response_blind():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "empirical" / "SNAPSHOT_JAPAN_GEOMETRY_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["scientific_freeze"]["r5b_status"] == "PASS"
    assert contract["focal_biology"]["species"] == "Cervus nippon"
    assert contract["focal_biology"]["state_space"] == ["adult", "juvenile"]
    assert contract["training_camera_roles"]["roles_are_mutually_exclusive"] is True
    assert contract["training_camera_roles"]["direct_state_composition_heldout_exposure"] == 0
    assert contract["firewall"]["response_payload_requests"] == 0
    assert contract["firewall"]["response_header_requests"] == 0
    assert contract["firewall"]["response_rows_opened"] == 0
    assert contract["firewall"]["response_values_opened"] is False
