from __future__ import annotations

import json
from pathlib import Path
import zipfile

from scripts.inventory_e5_sumatra_s1 import inventory

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_SUMATRA_S1_INVENTORY_CONTRACT.json"

def test_contract_is_inventory_only():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert value["status"] == "FROZEN_INVENTORY_NOT_AUTHORIZED"
    fw = value["response_firewall"]
    assert fw["archive_member_name_listing_authorized"] is True
    assert fw["readme_like_text_members_authorized"] is True
    assert fw["data_member_opening_authorized"] is False
    assert fw["expected_data_rows_read"] == 0
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False

def test_inventory_never_opens_data_rows(tmp_path):
    p = tmp_path / "s1.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("README.txt", "metadata.csv = deployment metadata\ndetections.csv = response\n")
        z.writestr("metadata.csv", b"\xff\xfe\x00must-not-open")
        z.writestr("detections.csv", b"\xff\xfe\x00must-not-open")
    value = inventory(p)
    assert value["response_boundary"]["readme_members_opened"] == ["README.txt"]
    assert value["response_boundary"]["non_readme_members_opened"] == []
    assert value["response_boundary"]["data_rows_read"] == 0
    assert value["response_boundary"]["response_rows_read"] == 0
    assert value["decision"]["candidate_qualified"] is False
