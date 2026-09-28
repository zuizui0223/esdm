from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "ODSP_LATTICE_READY_E2E_BINDING_V1.json"


def _read() -> dict[str, object]:
    return json.loads(BINDING.read_text(encoding="utf-8"))


def test_lattice_smoke_pins_current_esdm_and_odsp_versions():
    binding = _read()

    assert binding["esdm_protocol_merge_sha"] == (
        "ced6cd9ba4d50264c1f9d99fd097e4277fddfc3e"
    )
    assert binding["odsp"]["pinned_commit"] == (
        "0bd83e1ebb372c48839654ab0e42124fe37b8faf"
    )


def test_lattice_smoke_uses_complete_two_block_fixture():
    fixture = _read()["fixture"]

    assert fixture["base_information"] == ["suitability"]
    assert fixture["information_blocks"] == [
        {"name": "activity", "variables": ["activity"]},
        {"name": "state", "variables": ["state"]},
    ]
    assert fixture["independent_groups"] == ["g1", "g2"]
    assert fixture["validation_blocks_per_group"] == 4
    assert fixture["node_scores"] == {
        "base": 0.0,
        "activity": 0.4,
        "state": 0.1,
        "activity_state": 0.3,
    }


def test_lattice_smoke_freezes_order_sensitive_expected_result():
    expected = _read()["expected"]

    assert expected["node_count"] == 4
    assert expected["edge_count"] == 4
    assert expected["full_vs_base_gain_category"] == "generalizing"
    assert expected["point_path_status"] == "order_sensitive_full_transfer"
    assert expected["point_full_transfer_path_count"] == 1
    assert expected["point_total_admissible_path_count"] == 2
    assert expected["certified_path_status"] == "order_sensitive_full_transfer"
    assert expected["certified_robust_full_transfer_path_count"] == 1
    assert expected["all_cells_estimable"] is True
    assert expected["block_status"] == {
        "activity": "order_robust_generalizing",
        "state": "order_sensitive",
    }
    assert expected["shapley_can_override_edge_failure"] is False


def test_lattice_smoke_is_integration_only():
    boundary = _read()["boundary"]

    assert boundary["scientific_result"] is False
    assert boundary["transfer_source_registry_entry_created"] is False
    assert boundary["current_frozen_source_promoted"] is False
    assert boundary["current_eog_mainline_consumption"] is False
    assert boundary["n4_action_authorized"] is False
