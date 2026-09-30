from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_sumatra_focal_row1 import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_SUMATRA_FOCAL_ROW1_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-sumatra-focal-row1-once.yml"
)


def _xlsx_bytes():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        z.writestr(
            "xl/worksheets/sheet1.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <dimension ref="A1:H999"/>
            <sheetData>
              <row r="1">
                <c r="A1" t="s"><v>10</v></c>
                <c r="B1" t="s"><v>11</v></c>
                <c r="C1" t="inlineStr"><is><t>camera_id</t></is></c>
                <c r="D1" t="s"><v>12</v></c>
              </row>
              <row r="2"><c r="A2" t="s"><v>999</v></c></row>
            </sheetData>
            </worksheet>""",
        )
        z.writestr("xl/sharedStrings.xml", b"\xff\xfe\x00must-not-open")
        z.writestr(
            "xl/worksheets/sheet9.xml",
            b"\xff\xfe\x00site-cov-must-not-open",
        )
    return payload.getvalue()


def _outer(path: Path):
    xlsx = _xlsx_bytes()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Iding_spc_data.xlsx", xlsx)
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    value["source"]["archive_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    value["source"]["workbook_sha256"] = hashlib.sha256(xlsx).hexdigest()
    local = path.with_name("contract.json")
    local.write_text(json.dumps(value), encoding="utf-8")
    return local


def test_contract_allows_only_focal_row1_schema_not_values():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["focal_species_worksheet_xml_open_authorized"] is True
    assert fw["focal_species_row1_parse_authorized"] is True
    assert fw["row1_shared_string_indices_authorized"] is True
    assert fw["shared_strings_xml_open_authorized"] is False
    assert fw["worksheet_rows_after_row1_parse_authorized"] is False
    assert fw["focal_response_values_authorized"] is False


def test_focal_row1_precheck_reports_schema_only(tmp_path):
    archive = tmp_path / "s1.zip"
    local_contract = _outer(archive)
    value = precheck(archive, local_contract)

    structure = value["focal_species_row1_structure"]
    assert structure["dimension_ref"] == "A1:H999"
    assert structure["row1"]["cell_count"] == 4
    assert structure["shared_string_header_indices"] == ["10", "11", "12"]
    assert structure["inline_string_headers"] == ["camera_id"]
    assert structure["header_resolution_requires_shared_strings"] is True

    boundary = value["response_boundary"]
    assert boundary["opened_worksheet_members"] == ["xl/worksheets/sheet1.xml"]
    assert boundary["other_worksheet_members_opened"] == []
    assert boundary["shared_strings_opened"] is False
    assert boundary["worksheet_rows_parsed"] == 1
    assert boundary["rows_after_row1_parsed"] == 0
    assert boundary["data_rows_read"] == 0
    assert boundary["response_rows_read"] == 0
    assert boundary["focal_response_values_read"] == 0


def test_workflow_is_pure_marker_and_keeps_response_values_forbidden():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-focal-row1-v1" in text
    assert "E5_SUMATRA_FOCAL_ROW1_AUTHORIZED.json" in text
    assert "72f0c62403cd670f805ae6148a67b638c061dc1c" in text
    assert "workflow_dispatch" not in text
    assert "shared_strings_opening_authorized" in text
    assert "rows_after_row1_authorized" in text
    assert "focal_response_values_authorized" in text
