from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_UWIN_ZENODO_INVENTORY_CONTRACT.json"
)
STOP = (
    ROOT / "docs" / "replication" / "E5_UWIN_DRYAD_INVENTORY_TRANSPORT_STOP.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-uwin-zenodo-inventory-once.yml"
)


def test_dryad_inventory_stop_is_terminal_transport_only():
    value = json.loads(STOP.read_text(encoding="utf-8"))
    assert value["status"] == "TERMINAL_TRANSPORT_STOP_NO_PACKAGE_READ"
    assert value["response_boundary"]["archive_inventory_executed"] is False
    assert value["response_boundary"]["readme_members_opened"] == 0
    assert value["response_boundary"]["data_rows_read"] == 0
    assert value["governance"]["same_authorization_rerun_allowed"] is False
    assert value["governance"]["candidate_scientific_status_changed"] is False


def test_zenodo_mirror_contract_keeps_readme_only_firewall():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert value["status"] == "FROZEN_INVENTORY_NOT_AUTHORIZED"
    assert value["source"]["expected_md5"] == "72c6e7d51f359e84e2e49154942b4c98"
    assert value["response_firewall"]["readme_members_read_authorized"] is True
    assert value["response_firewall"]["non_readme_member_opening_authorized"] is False
    assert value["response_firewall"]["data_rows_read_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_zenodo_workflow_is_separate_pure_marker_route():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/uwin-zenodo-inventory-v1" in text
    assert "E5_UWIN_ZENODO_INVENTORY_AUTHORIZED.json" in text
    assert "zenodo.org/records/6366482/files/Gallo_eLife_DryadData.zip" in text
    assert "72c6e7d51f359e84e2e49154942b4c98" in text
    assert "1e196151031bfd481ca0df640973b17075e7ff7e" in text
    assert "workflow_dispatch" not in text
    assert "non_readme_member_opening_authorized" in text
