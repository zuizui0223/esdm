from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_sumatra_sitecov_row1 import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_SUMATRA_SITECOV_ROW1_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-sumatra-sitecov-row1-once.yml"
)


def _xlsx_bytes():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        z.writestr(
            "xl/worksheets/sheet9.xml",
            """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
            <dimension ref="A1:C999"/>
            <sheetData>
              <row r="1">
                <c r="A1" t="s"><v>7</v></c>
                <c r="B1" t="inlineStr"><is><t>camera_brand</t></is></c>
                <c r="C1" t="s" s="2"><v>9</v></c>
              </row>
              <row r="2"><c r="A2"><v>999999</v></c></row>
            </sheetData>
            </worksheet>""",
        )
        z.writestr("xl/sharedStrings.xml", b"\xff\xfe\x00must-not-open")
        z.writestr(
            "xl/worksheets/sheet1.xml",
            b"\xff\xfe\x00response-sheet-must-not-open",
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


def test_contract_allows_only_site_cov_row1_not_shared_strings_or_data_rows():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["site_cov_worksheet_xml_open_authorized"] is True
    assert fw["site_cov_row1_parse_authorized"] is True
    assert fw["row1_shared_string_indices_authorized"] is True
    assert fw["shared_strings_xml_open_authorized"] is False
    assert fw["worksheet_rows_after_row1_parse_authorized"] is False
    assert fw["row2_or_later_values_authorized"] is False
    assert fw["data_rows_read_authorized"] is False


def test_row1_precheck_reports_structure_without_resolving_shared_strings(tmp_path):
    archive = tmp_path / "s1.zip"
    local_contract = _outer(archive)
    value = precheck(archive, local_contract)

    structure = value["site_cov_row1_structure"]
    assert structure["dimension_ref"] == "A1:C999"
    assert structure["row1"]["cell_count"] == 3
    assert structure["shared_string_header_indices"] == ["7", "9"]
    assert structure["inline_string_headers"] == ["camera_brand"]
    assert structure["header_resolution_requires_shared_strings"] is True

    boundary = value["response_boundary"]
    assert boundary["opened_worksheet_members"] == ["xl/worksheets/sheet9.xml"]
    assert boundary["other_worksheet_members_opened"] == []
    assert boundary["shared_strings_opened"] is False
    assert boundary["worksheet_rows_parsed"] == 1
    assert boundary["rows_after_row1_parsed"] == 0
    assert boundary["data_rows_read"] == 0
    assert boundary["numeric_data_values_read"] == 0
    assert boundary["response_rows_read"] == 0


def test_workflow_is_pure_marker_and_keeps_shared_strings_forbidden():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-sitecov-row1-v1" in text
    assert "E5_SUMATRA_SITECOV_ROW1_AUTHORIZED.json" in text
    assert "ce2febfb193f563e0943ddae89468d87526cf7b0" in text
    assert "workflow_dispatch" not in text
    assert "shared_strings_opening_authorized" in text
    assert "rows_after_row1_authorized" in text
    assert "precheck_e5_sumatra_sitecov_row1.py" in text
