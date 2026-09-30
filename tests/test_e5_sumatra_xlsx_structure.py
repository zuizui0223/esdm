from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_sumatra_xlsx_structure import precheck

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_SUMATRA_XLSX_STRUCTURE_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-sumatra-xlsx-structure-once.yml"


def _xlsx_bytes():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        z.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="metadata" sheetId="1" r:id="rId1"/></sheets></workbook>'
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
            '</Relationships>'
        )
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr(
            "xl/tables/table1.xml",
            '<table name="Meta" displayName="Meta" ref="A1:B3">'
            '<tableColumns count="2"><tableColumn id="1" name="station_id"/>'
            '<tableColumn id="2" name="camera_brand"/></tableColumns></table>'
        )
        z.writestr("xl/worksheets/sheet1.xml", b"\xff\xfe\x00must-not-open")
        z.writestr("xl/sharedStrings.xml", b"\xff\xfe\x00response-strings-must-not-open")
    return payload.getvalue()


def _outer(path: Path, contract_path: Path):
    xlsx = _xlsx_bytes()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Iding_spc_data.xlsx", xlsx)
        z.writestr("analysis.R", "species_response <- TRUE")
    value = json.loads(contract_path.read_text(encoding="utf-8"))
    value["source"]["archive_sha256"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    local = path.with_name("contract.json")
    local.write_text(json.dumps(value), encoding="utf-8")
    return local


def test_contract_forbids_shared_strings_worksheets_and_rows():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["shared_string_table_opening_authorized"] is False
    assert fw["worksheet_rows_after_row1_authorized"] is False
    assert fw["cell_numeric_values_authorized"] is False
    assert fw["r_script_opening_authorized"] is False
    assert fw["data_rows_read_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_structure_precheck_reads_metadata_xml_but_no_worksheet_or_shared_strings(tmp_path):
    archive = tmp_path / "s1.zip"
    local_contract = _outer(archive, CONTRACT)
    result = precheck(archive, local_contract)
    b = result["response_boundary"]

    assert result["xlsx_structure"]["worksheets"][0]["name"] == "metadata"
    assert result["xlsx_structure"]["structured_tables"][0]["declared_columns"] == [
        "station_id", "camera_brand"
    ]
    assert result["xlsx_structure"]["shared_strings_member_present"] is True
    assert b["shared_strings_opened"] is False
    assert b["worksheet_cell_xml_opened"] is False
    assert b["worksheet_rows_read"] == 0
    assert b["cell_values_read"] == 0
    assert b["data_rows_read"] == 0
    assert b["response_rows_read"] == 0
    assert b["r_scripts_opened"] is False


def test_workflow_is_pure_marker_and_has_no_response_path():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-xlsx-structure-precheck-v1" in text
    assert "E5_SUMATRA_XLSX_STRUCTURE_AUTHORIZED.json" in text
    assert "0c1800284c1db7ebed293042a62bb203a2fde345" in text
    assert "workflow_dispatch" not in text
    assert "shared_strings_opening_authorized" in text
    assert "worksheet_cell_opening_authorized" in text
