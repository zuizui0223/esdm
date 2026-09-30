from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

from scripts.inventory_e5_uwin_dryad_package import inventory


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_UWIN_PACKAGE_INVENTORY_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-uwin-package-inventory-once.yml"
)


def _archive(path: Path, *, include_readme=True):
    with zipfile.ZipFile(path, "w") as z:
        if include_readme:
            z.writestr(
                "GalloData/README.txt",
                "site_metadata.csv = response-independent sites\n"
                "detections.csv = species detections\n",
            )
        z.writestr("GalloData/site_metadata.csv", b"\xff\xfe\x00must-not-open")
        z.writestr("GalloData/detections.csv", b"\xff\xfe\x00must-not-open")
    return path


def test_inventory_contract_is_readme_only_and_nonqualifying():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    firewall = value["response_firewall"]
    assert value["status"] == "FROZEN_INVENTORY_NOT_AUTHORIZED"
    assert firewall["archive_member_name_listing_authorized"] is True
    assert firewall["readme_members_read_authorized"] is True
    assert firewall["csv_xlsx_rdata_rds_data_member_opening_authorized"] is False
    assert firewall["response_table_opening_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_inventory_opens_readme_but_never_data_tables(tmp_path):
    result = inventory(_archive(tmp_path / "candidate.zip"))
    boundary = result["response_boundary"]
    assert boundary["readme_members_opened"] == ["GalloData/README.txt"]
    assert boundary["non_readme_members_opened"] == []
    assert boundary["data_rows_read"] == 0
    assert boundary["response_rows_read"] == 0
    assert result["data_like_members_present_but_unopened"] == [
        "GalloData/detections.csv",
        "GalloData/site_metadata.csv",
    ]
    assert result["decision"]["candidate_qualified"] is False


def test_inventory_never_opens_binary_csv_even_when_no_readme(tmp_path):
    result = inventory(_archive(tmp_path / "candidate.zip", include_readme=False))
    assert result["response_boundary"]["readme_members_opened"] == []
    assert result["response_boundary"]["non_readme_members_opened"] == []
    assert result["response_boundary"]["data_rows_read"] == 0


def test_workflow_is_pure_marker_one_shot_and_pins_public_package():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/uwin-package-inventory-v1" in text
    assert "E5_UWIN_PACKAGE_INVENTORY_AUTHORIZED.json" in text
    assert "1387569" in text
    assert "72c6e7d51f359e84e2e49154942b4c98" in text
    assert "9f8556c0df7c8999c37015dae00d58ff11dec2e3" in text
    assert "workflow_dispatch" not in text
    assert "non_readme_member_opening_authorized" in text
