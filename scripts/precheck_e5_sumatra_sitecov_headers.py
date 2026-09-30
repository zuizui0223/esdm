#!/usr/bin/env python3
"""Resolve only pre-frozen site_cov header shared-string indices for E5 Sumatra."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-sumatra-sitecov-header-sharedstrings-response-blind-v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _resolve_targets(stream, targets: set[int], max_target: int) -> tuple[dict[int, str], int]:
    resolved: dict[int, str] = {}
    index = -1
    traversed = 0

    for event, elem in ET.iterparse(stream, events=("end",)):
        if _local(elem.tag) != "si":
            continue

        index += 1
        traversed += 1

        if index in targets:
            pieces = []
            for child in elem.iter():
                if _local(child.tag) == "t" and child.text is not None:
                    pieces.append(child.text)
            resolved[index] = "".join(pieces)

        # Important: never retain/report non-target values.
        elem.clear()

        if index >= max_target and targets.issubset(resolved):
            break

    if set(resolved) != targets:
        missing = sorted(targets - set(resolved))
        raise ValueError(f"target shared-string indices did not resolve: {missing!r}")

    return resolved, traversed


def _classify_header(name: str, contract: dict) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower())
    bearing = tuple(contract["schema_only_header_rule"]["response_bearing_header_name_patterns"])
    independent = tuple(
        contract["schema_only_header_rule"]["response_independent_header_name_patterns"]
    )
    if any(token in normalized for token in bearing):
        return "POTENTIALLY_RESPONSE_BEARING"
    if any(token in normalized for token in independent):
        return "POTENTIALLY_RESPONSE_INDEPENDENT"
    return "UNCLASSIFIED"


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Sumatra header resolver contract")

    firewall = contract["response_firewall"]
    if firewall.get("target_indices_frozen_before_opening") is not True:
        raise ValueError("target indices must be frozen before sharedStrings opening")
    for key in (
        "non_target_string_values_may_be_retained",
        "non_target_string_values_may_be_reported",
        "shared_strings_after_max_target_may_be_parsed",
        "worksheet_xml_open_authorized",
        "site_cov_data_rows_authorized",
        "species_sheet_opening_authorized",
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

    shared_member = contract["source"]["shared_strings_member"]
    targets = {int(value) for value in contract["source"]["target_shared_string_indices"]}
    max_target = int(contract["source"]["max_target_index"])

    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as xlsx:
        if shared_member not in xlsx.namelist():
            raise ValueError("sharedStrings.xml missing")
        with xlsx.open(shared_member, "r") as stream:
            resolved, traversed = _resolve_targets(stream, targets, max_target)

    cells = contract["source"]["target_cells"]
    indices = contract["source"]["target_shared_string_indices"]
    if len(cells) != len(indices):
        raise ValueError("target cell/index geometry drifted")

    headers = []
    for cell, index in zip(cells, indices, strict=True):
        numeric = int(index)
        value = resolved[numeric]
        headers.append({
            "cell": str(cell),
            "shared_string_index": numeric,
            "header": value,
            "schema_classification": _classify_header(value, contract),
        })

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "sumatra_mesopredator_paired_2014_2015",
        "precheck_id": "e5-sumatra-sitecov-header-resolver-result-v1",
        "status": "E5_RESPONSE_BLIND_SITECOV_HEADER_RESOLUTION",
        "source": {
            "archive_sha256": archive_sha,
            "workbook_member": workbook_member,
            "workbook_sha256": workbook_sha,
            "shared_strings_member": shared_member,
        },
        "frozen_targets": {
            "cells": list(cells),
            "shared_string_indices": [int(v) for v in indices],
            "max_target_index": max_target,
        },
        "resolved_headers": headers,
        "streaming_scan": {
            "shared_string_entries_traversed": traversed,
            "expected_traversed_through_index": max_target + 1,
            "target_count": len(targets),
            "target_count_resolved": len(resolved),
            "non_target_values_retained": 0,
            "non_target_values_reported": 0,
            "entries_after_max_target_parsed": 0,
        },
        "response_boundary": {
            "shared_strings_opened": True,
            "worksheet_xml_opened": False,
            "site_cov_data_rows_read": 0,
            "species_sheet_rows_read": 0,
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
            "separate_child_contract_required_before_site_cov_data_rows": True,
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
