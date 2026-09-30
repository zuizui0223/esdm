#!/usr/bin/env python3
"""Response-blind row-1 structure precheck for the Sumatra site_cov worksheet."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-sumatra-sitecov-row1-response-blind-precheck-v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _parse_site_cov_row1(stream) -> dict[str, object]:
    dimension_ref = None
    row1 = None

    for event, elem in ET.iterparse(stream, events=("start", "end")):
        name = _local(elem.tag)

        if event == "start" and name == "dimension" and dimension_ref is None:
            dimension_ref = str(elem.attrib.get("ref", ""))

        if event != "end" or name != "row":
            continue

        row_number = str(elem.attrib.get("r", ""))
        if row_number != "1":
            raise ValueError(
                "site_cov first parsed worksheet row is not row 1; fail closed"
            )

        cells = []
        for cell in list(elem):
            if _local(cell.tag) != "c":
                continue
            cell_type = str(cell.attrib.get("t", ""))
            record = {
                "reference": str(cell.attrib.get("r", "")),
                "type": cell_type,
                "style_index": str(cell.attrib.get("s", "")),
                "shared_string_index": None,
                "inline_string_header": None,
            }

            if cell_type == "s":
                for child in list(cell):
                    if _local(child.tag) == "v":
                        raw = (child.text or "").strip()
                        record["shared_string_index"] = raw if raw else None
                        break
            elif cell_type == "inlineStr":
                texts = []
                for child in cell.iter():
                    if _local(child.tag) == "t" and child.text is not None:
                        texts.append(child.text)
                record["inline_string_header"] = "".join(texts)

            # Deliberately ignore numeric/string cell values for all other types.
            cells.append(record)

        row1 = {
            "row_number": 1,
            "cell_count": len(cells),
            "cells": cells,
        }
        break

    if row1 is None:
        raise ValueError("site_cov row 1 was not found")

    shared_indices = [
        cell["shared_string_index"]
        for cell in row1["cells"]
        if cell["shared_string_index"] is not None
    ]
    inline_headers = [
        cell["inline_string_header"]
        for cell in row1["cells"]
        if cell["inline_string_header"] is not None
    ]
    return {
        "dimension_ref": dimension_ref,
        "row1": row1,
        "shared_string_header_indices": shared_indices,
        "inline_string_headers": inline_headers,
        "header_resolution_requires_shared_strings": bool(shared_indices),
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Sumatra site_cov row1 contract")

    firewall = contract["response_firewall"]
    for key in (
        "worksheet_rows_after_row1_parse_authorized",
        "shared_strings_xml_open_authorized",
        "other_worksheet_xml_open_authorized",
        "row2_or_later_values_authorized",
        "numeric_data_values_authorized",
        "r_script_opening_authorized",
        "data_rows_read_authorized",
        "response_rows_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    archive_raw = archive_path.read_bytes()
    archive_sha = _sha256(archive_raw)
    if archive_sha != contract["source"]["archive_sha256"]:
        raise ValueError("outer archive SHA256 drifted")

    workbook_member = contract["source"]["workbook_member"]
    with zipfile.ZipFile(io.BytesIO(archive_raw)) as outer:
        if workbook_member not in outer.namelist():
            raise ValueError("pinned workbook member missing")
        workbook_bytes = outer.read(workbook_member)

    workbook_sha = _sha256(workbook_bytes)
    if workbook_sha != contract["source"]["workbook_sha256"]:
        raise ValueError("workbook SHA256 drifted")

    worksheet_member = contract["source"]["worksheet_member"]
    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as xlsx:
        names = set(xlsx.namelist())
        if worksheet_member not in names:
            raise ValueError("site_cov worksheet member missing")

        # Only the declared site_cov worksheet stream is opened.
        with xlsx.open(worksheet_member, "r") as stream:
            structure = _parse_site_cov_row1(stream)

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "sumatra_mesopredator_paired_2014_2015",
        "precheck_id": "e5-sumatra-sitecov-row1-precheck-result-v1",
        "status": "E5_RESPONSE_BLIND_SITECOV_ROW1_PRECHECK",
        "source": {
            "archive_sha256": archive_sha,
            "workbook_member": workbook_member,
            "workbook_sha256": workbook_sha,
            "worksheet_name": contract["source"]["worksheet_name"],
            "worksheet_member": worksheet_member,
        },
        "site_cov_row1_structure": structure,
        "response_boundary": {
            "opened_worksheet_members": [worksheet_member],
            "other_worksheet_members_opened": [],
            "shared_strings_opened": False,
            "worksheet_rows_parsed": 1,
            "rows_after_row1_parsed": 0,
            "data_rows_read": 0,
            "response_rows_read": 0,
            "numeric_data_values_read": 0,
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
            "separate_child_contract_required_before_shared_strings_or_site_cov_data_rows": True,
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
