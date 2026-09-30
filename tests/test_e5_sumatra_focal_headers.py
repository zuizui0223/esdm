from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

from scripts.precheck_e5_sumatra_focal_headers import precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_SUMATRA_FOCAL_HEADERS_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-sumatra-focal-headers-once.yml"
)


def _xlsx_bytes():
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as z:
        strings = [
            "<si><t>station_id</t></si>",
            "<si><t>camera_id</t></si>",
            "<si><t>datetime</t></si>",
            "<si><t>species</t></si>",
            "<si><t>camera_side</t></si>",
            "<si><t>must_not_parse_after_target</t></si>",
        ]
        z.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            + "".join(strings)
            + "</sst>",
        )
        z.writestr(
            "xl/worksheets/sheet1.xml",
            b"\xff\xfe\x00focal-data-must-not-open",
        )
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


def test_contract_freezes_first_five_header_indices_before_shared_strings_opening():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert value["source"]["target_shared_string_indices"] == [0, 1, 2, 3, 4]
    assert value["source"]["max_target_index"] == 4
    fw = value["response_firewall"]
    assert fw["target_indices_frozen_before_opening"] is True
    assert fw["only_target_string_values_may_be_retained"] is True
    assert fw["non_target_string_values_may_be_retained"] is False
    assert fw["shared_strings_after_max_target_may_be_parsed"] is False
    assert fw["focal_species_data_rows_authorized"] is False
    assert fw["focal_response_values_authorized"] is False


def test_resolver_reads_only_first_five_headers_and_stops(tmp_path):
    archive = tmp_path / "s1.zip"
    local_contract = _outer(archive)
    value = precheck(archive, local_contract)

    headers = [row["header"] for row in value["resolved_headers"]]
    assert headers == [
        "station_id",
        "camera_id",
        "datetime",
        "species",
        "camera_side",
    ]

    viability = value["viability_questions"]
    assert viability["station_or_location_identifier_header_present"] is True
    assert viability["event_timestamp_header_present"] is True
    assert viability["individual_camera_identifier_header_present"] is True
    assert viability["paired_sensor_or_camera_side_header_present"] is True
    assert viability["species_or_taxon_header_present"] is True

    scan = value["streaming_scan"]
    assert scan["shared_string_entries_traversed"] == 5
    assert scan["target_count_resolved"] == 5
    assert scan["non_target_values_retained"] == 0
    assert scan["non_target_values_reported"] == 0
    assert scan["entries_after_max_target_parsed"] == 0

    serialized = json.dumps(value)
    assert "must_not_parse_after_target" not in serialized

    boundary = value["response_boundary"]
    assert boundary["worksheet_xml_opened"] is False
    assert boundary["focal_species_data_rows_read"] == 0
    assert boundary["other_species_sheet_rows_read"] == 0
    assert boundary["site_cov_data_rows_read"] == 0
    assert boundary["data_rows_read"] == 0
    assert boundary["response_rows_read"] == 0
    assert boundary["focal_response_values_read"] == 0


def test_workflow_pins_first_five_indices_and_forbids_data_rows():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/sumatra-focal-headers-v1" in text
    assert "E5_SUMATRA_FOCAL_HEADERS_AUTHORIZED.json" in text
    assert "df6824b8e09b999799425173f1f1bedcdca99642" in text
    assert "[0, 1, 2, 3, 4]" in text
    assert "workflow_dispatch" not in text
    assert "focal_species_data_rows_authorized" in text
    assert "focal_response_values_authorized" in text
