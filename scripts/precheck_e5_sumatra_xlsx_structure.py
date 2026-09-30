#!/usr/bin/env python3
"""Response-blind structural precheck of the Sumatra S1 XLSX workbook.

The workbook container may be opened, but worksheet cell data and shared strings are
never read. Only workbook metadata/relationships and structured-table definitions
are parsed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET


ALLOWED_EXACT = {
    "[Content_Types].xml",
    "xl/workbook.xml",
    "xl/_rels/workbook.xml.rels",
}
ALLOWED_PREFIXES = ("xl/tables/",)
FORBIDDEN_EXACT = {"xl/sharedStrings.xml"}
FORBIDDEN_PREFIXES = (
    "xl/worksheets/",
    "xl/comments",
    "xl/threadedComments/",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _find_member(names: list[str], basename: str) -> str:
    matches = [
        name for name in names
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {basename!r}: {matches!r}")
    return matches[0]


def _sheet_metadata(xml_bytes: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    output = []
    for element in root.iter():
        if _local(element.tag) != "sheet":
            continue
        rel_id = ""
        for key, value in element.attrib.items():
            if _local(key) == "id":
                rel_id = str(value)
                break
        output.append({
            "name": str(element.attrib.get("name", "")),
            "sheetId": str(element.attrib.get("sheetId", "")),
            "relationship_id": rel_id,
            "state": str(element.attrib.get("state", "visible")),
        })
    return output


def _relationships(xml_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(xml_bytes)
    output = {}
    for element in root:
        if _local(element.tag) != "Relationship":
            continue
        rel_id = str(element.attrib.get("Id", ""))
        target = str(element.attrib.get("Target", ""))
        if rel_id:
            output[rel_id] = target
    return output


def _table_definition(xml_bytes: bytes, member: str) -> dict[str, object]:
    root = ET.fromstring(xml_bytes)
    columns = []
    for element in root.iter():
        if _local(element.tag) == "tableColumn":
            columns.append(str(element.attrib.get("name", "")))
    return {
        "member": member,
        "table_name": str(root.attrib.get("name", "")),
        "display_name": str(root.attrib.get("displayName", "")),
        "reference": str(root.attrib.get("ref", "")),
        "declared_columns": columns,
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != (
        "e5-sumatra-xlsx-structure-response-blind-precheck-v1"
    ):
        raise ValueError("unexpected Sumatra XLSX contract")
    firewall = contract["response_firewall"]
    for key in (
        "shared_string_table_opening_authorized",
        "worksheet_rows_after_row1_authorized",
        "cell_numeric_values_authorized",
        "r_script_opening_authorized",
        "data_rows_read_authorized",
        "response_rows_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    archive_raw = archive_path.read_bytes()
    observed_archive_sha = _sha256(archive_raw)
    expected_archive_sha = contract["source"]["archive_sha256"]
    if observed_archive_sha != expected_archive_sha:
        raise ValueError(
            f"outer archive SHA256 drift: {observed_archive_sha} != {expected_archive_sha}"
        )

    opened_xlsx_members: list[str] = []
    with zipfile.ZipFile(io.BytesIO(archive_raw)) as outer:
        outer_names = sorted(
            name for name in outer.namelist() if not name.endswith("/")
        )
        workbook_member = contract["source"]["workbook_member"]
        if workbook_member not in outer_names:
            raise ValueError("pinned workbook member missing")
        workbook_bytes = outer.read(workbook_member)

    workbook_sha = _sha256(workbook_bytes)
    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as xlsx:
        xlsx_names = sorted(
            name for name in xlsx.namelist() if not name.endswith("/")
        )
        for forbidden in FORBIDDEN_EXACT:
            if forbidden in opened_xlsx_members:
                raise AssertionError("forbidden XLSX member opened")
        workbook_xml = xlsx.read("xl/workbook.xml")
        opened_xlsx_members.append("xl/workbook.xml")
        rels_xml = xlsx.read("xl/_rels/workbook.xml.rels")
        opened_xlsx_members.append("xl/_rels/workbook.xml.rels")
        content_types = xlsx.read("[Content_Types].xml")
        opened_xlsx_members.append("[Content_Types].xml")

        sheets = _sheet_metadata(workbook_xml)
        rels = _relationships(rels_xml)
        for sheet in sheets:
            sheet["target"] = rels.get(sheet["relationship_id"], "")

        tables = []
        for member in xlsx_names:
            if member.startswith("xl/tables/") and member.endswith(".xml"):
                data = xlsx.read(member)
                opened_xlsx_members.append(member)
                tables.append(_table_definition(data, member))

    if "xl/sharedStrings.xml" in opened_xlsx_members:
        raise AssertionError("sharedStrings.xml must never be opened")
    if any(name.startswith("xl/worksheets/") for name in opened_xlsx_members):
        raise AssertionError("worksheet cell XML must never be opened")
    if any(
        name not in ALLOWED_EXACT
        and not any(name.startswith(prefix) for prefix in ALLOWED_PREFIXES)
        for name in opened_xlsx_members
    ):
        raise AssertionError("unexpected XLSX member was opened")

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "sumatra_mesopredator_paired_2014_2015",
        "precheck_id": "e5-sumatra-xlsx-structure-precheck-result-v1",
        "status": "E5_RESPONSE_BLIND_XLSX_STRUCTURE_PRECHECK",
        "source": {
            "archive_sha256": observed_archive_sha,
            "workbook_member": contract["source"]["workbook_member"],
            "workbook_sha256": workbook_sha,
        },
        "xlsx_structure": {
            "member_count": len(xlsx_names),
            "member_names": xlsx_names,
            "worksheets": sheets,
            "structured_tables": tables,
            "shared_strings_member_present": "xl/sharedStrings.xml" in xlsx_names,
            "worksheet_members_present": [
                name for name in xlsx_names if name.startswith("xl/worksheets/")
            ],
        },
        "response_boundary": {
            "opened_xlsx_members": opened_xlsx_members,
            "shared_strings_opened": False,
            "worksheet_cell_xml_opened": False,
            "worksheet_rows_read": 0,
            "cell_values_read": 0,
            "data_rows_read": 0,
            "response_rows_read": 0,
            "r_scripts_opened": False,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_child_contract_required_before_shared_strings_or_rows": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = precheck(args.archive, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
