from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_sumatra_sitecov_headers import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_SUMATRA_SITECOV_HEADERS_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-sumatra-sitecov-headers-once.yml"
)


def _xlsx_bytes():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        strings = []
        for i in range(354):
            strings.append(f"<si><t>secret_species_{i}</t></si>")
        strings += [
            "<si><t>site_id</t></si>",
            "<si><t>elevation</t></si>",
            "<si><t>distance_road</t></si>",
            "<si><t>camera_brand</t></si>",
            "<si><t>must_not_parse_after_target</t></si>",
        ]
        z.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            + "".join(strings)
            + "</sst>",
        )
        z.writestr(
            "xl/worksheets/sheet9.xml",
            b"\xff\xfe\x00site-data-must-not-open",
        )
        z.writestr(
            "xl/worksheets/sheet1.xml",
            b"\xff\xfe\x00species-sheet-must-not-open",
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


def test_contract_freezes_target_indices_before_shared_strings_opening():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert value["source"]["target_shared_string_indices"] == [354, 355, 356, 357]
    assert value["source"]["max_target_index"] == 357
    fw = value["response_firewall"]
    assert fw["target_indices_frozen_before_opening"] is True
    assert fw["only_target_string_values_may_be_retained"] is True
    assert fw["non_target_string_values_may_be_retained"] is False
    assert fw["shared_strings_after_max_target_may_be_parsed"] is False
    assert fw["site_cov_data_rows_authorized"] is False


def test_resolver_keeps_only_target_headers_and_stops_at_max_target(tmp_path):
    archive = tmp_path / "s1.zip"
    local_contract = _outer(archive)
    value = precheck(archive, local_contract)

    headers = [row["header"] for row in value["resolved_headers"]]
    assert headers == ["site_id", "elevation", "distance_road", "camera_brand"]

    scan = value["streaming_scan"]
    assert scan["shared_string_entries_traversed"] == 358
    assert scan["target_count_resolved"] == 4
    assert scan["non_target_values_retained"] == 0
    assert scan["non_target_values_reported"] == 0
    assert scan["entries_after_max_target_parsed"] == 0

    serialized = json.dumps(value)
    assert "secret_species_" not in serialized
    assert "must_not_parse_after_target" not in serialized

    boundary = value["response_boundary"]
    assert boundary["shared_strings_opened"] is True
    assert boundary["worksheet_xml_opened"] is False
    assert boundary["site_cov_data_rows_read"] == 0
    assert boundary["species_sheet_rows_read"] == 0
    assert boundary["response_rows_read"] == 0


def test_workflow_pins_indices_and_forbids_data_rows():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-sitecov-headers-v1" in text
    assert "E5_SUMATRA_SITECOV_HEADERS_AUTHORIZED.json" in text
    assert "99f9fe5c425efe92f80f28b0bda5ade5bb269e47" in text
    assert "[354, 355, 356, 357]" in text
    assert "workflow_dispatch" not in text
    assert "site_cov_data_rows_authorized" in text
