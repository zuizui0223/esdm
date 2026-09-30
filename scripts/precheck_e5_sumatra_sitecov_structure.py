#!/usr/bin/env python3
"""Inspect only structural metadata from Sumatra's response-independent site_cov sheet."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


CELL_REF_RE = re.compile(r"^([A-Z]+)([0-9]+)$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _column_number(letters: str) -> int:
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - 64)
    return value


def _dimension_geometry(ref: str) -> dict[str, object]:
    raw = str(ref or "").strip()
    if not raw:
        return {"reference": "", "max_row": None, "max_column": None}
    tail = raw.split(":")[-1]
    match = CELL_REF_RE.match(tail)
    if match is None:
        return {"reference": raw, "max_row": None, "max_column": None}
    return {
        "reference": raw,
        "max_row": int(match.group(2)),
        "max_column": _column_number(match.group(1)),
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "e5-sumatra-sitecov-cell-structure-precheck-v1":
        raise ValueError("unexpected site_cov structure contract")
    fw = contract["response_firewall"]
    forbidden_true = (
        "row1_shared_string_value_authorized",
        "shared_strings_xml_opening_authorized",
        "row1_numeric_value_authorized",
        "row2_or_later_value_authorized",
        "any_cell_value_reporting_authorized",
        "formula_text_authorized",
        "other_worksheet_opening_authorized",
        "r_script_opening_authorized",
        "data_rows_read_authorized",
        "response_rows_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    )
    for key in forbidden_true:
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    archive_bytes = archive_path.read_bytes()
    archive_sha = _sha256(archive_bytes)
    if archive_sha != contract["source"]["archive_sha256"]:
        raise ValueError("outer archive SHA256 drifted")

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer:
        workbook_bytes = outer.read(contract["source"]["workbook_member"])
    workbook_sha = _sha256(workbook_bytes)
    if workbook_sha != contract["source"]["workbook_sha256"]:
        raise ValueError("workbook SHA256 drifted")

    sheet_member = contract["source"]["worksheet_member"]
    opened_xlsx_members = []
    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as xlsx:
        if sheet_member not in xlsx.namelist():
            raise ValueError("site_cov worksheet member missing")
        sheet_bytes = xlsx.read(sheet_member)
        opened_xlsx_members.append(sheet_member)

    root = ET.fromstring(sheet_bytes)
    dimension_ref = ""
    row1 = None
    for child in root:
        local = _local(child.tag)
        if local == "dimension":
            dimension_ref = str(child.attrib.get("ref", ""))
        elif local == "sheetData":
            for row in child:
                if _local(row.tag) != "row":
                    continue
                if str(row.attrib.get("r", "")) == "1":
                    row1 = row
                break

    cells = []
    if row1 is not None:
        for cell in row1:
            if _local(cell.tag) != "c":
                continue
            ref = str(cell.attrib.get("r", ""))
            cell_type = str(cell.attrib.get("t", ""))
            item = {
                "reference": ref,
                "type": cell_type,
                "shared_string_index": None,
            }
            if cell_type == "s":
                for child in cell:
                    if _local(child.tag) == "v":
                        raw = str(child.text or "").strip()
                        if raw:
                            if not raw.isdigit():
                                raise ValueError("row-1 shared-string reference is not integer")
                            item["shared_string_index"] = int(raw)
                        break
            cells.append(item)

    shared_indices = sorted({
        int(cell["shared_string_index"])
        for cell in cells
        if cell["shared_string_index"] is not None
    })

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "sumatra_mesopredator_paired_2014_2015",
        "precheck_id": "e5-sumatra-sitecov-cell-structure-result-v1",
        "status": "E5_RESPONSE_BLIND_SITECOV_STRUCTURE_PRECHECK",
        "source": {
            "archive_sha256": archive_sha,
            "workbook_sha256": workbook_sha,
            "worksheet_member": sheet_member,
            "worksheet_sha256": _sha256(sheet_bytes),
        },
        "site_cov_structure": {
            "dimension": _dimension_geometry(dimension_ref),
            "row1_cell_count": len(cells),
            "row1_cells": cells,
            "row1_shared_string_indices": shared_indices,
            "header_strings_decoded": False,
            "requires_selective_shared_string_child": bool(shared_indices),
        },
        "response_boundary": {
            "opened_xlsx_members": opened_xlsx_members,
            "shared_strings_opened": False,
            "other_worksheets_opened": False,
            "reported_numeric_cell_values": 0,
            "reported_row2_or_later_values": 0,
            "formula_text_read": False,
            "r_scripts_opened": False,
            "data_rows_read": 0,
            "response_rows_read": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_child_contract_required_before_decoding_header_strings_or_metadata_values": True,
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
