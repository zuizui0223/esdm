#!/usr/bin/env python3
"""Read exactly one CSV header line for the E5 Udzungwa candidate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re


EXPECTED_CONTRACT_ID = "e5-udzungwa-dat-v3-header-response-blind-v1"


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _present(headers: list[str], patterns: list[str]) -> bool:
    normalized = {_norm(v) for v in headers}
    tokens = {_norm(v) for v in patterns}
    return any(
        token == header or token in header
        for header in normalized
        for token in tokens
        if token
    )


def precheck(csv_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Udzungwa header contract")

    fw = contract["response_firewall"]
    if fw.get("csv_header_line_read_authorized") is not True:
        raise ValueError("header opening not authorized")
    for key in (
        "csv_second_line_or_later_read_authorized",
        "csv_data_rows_read_authorized",
        "species_response_values_authorized",
        "timestamp_values_authorized",
        "count_values_authorized",
        "effect_direction_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with csv_path.open("rb") as handle:
        # Hashing file bytes is permitted, but row parsing is not. The header parse below
        # opens a fresh stream and reads one line exactly.
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(block)
            sha.update(block)

    observed_md5 = md5.hexdigest()
    if observed_md5 != contract["source"]["expected_md5"]:
        raise ValueError(
            f"source MD5 drift: {observed_md5} != {contract['source']['expected_md5']}"
        )

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        header_line = handle.readline()
        if not header_line:
            raise ValueError("empty CSV")
        # Do not call readline again, iterate, or instantiate a DictReader on the file.
        headers = next(csv.reader([header_line]))

    patterns = contract["viability_patterns"]
    flags = {
        key: _present(headers, values)
        for key, values in patterns.items()
    }

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "udzungwa_paired_arrays_2013_2014",
        "precheck_id": "e5-udzungwa-dat-v3-header-result-v1",
        "status": "E5_RESPONSE_BLIND_HEADER_PRECHECK",
        "source": {
            "dataset_doi": contract["source"]["dataset_doi"],
            "file_name": contract["source"]["file_name"],
            "observed_md5": observed_md5,
            "observed_sha256": sha.hexdigest(),
        },
        "header": {
            "column_count": len(headers),
            "columns": headers,
            "normalized_columns": [_norm(v) for v in headers],
        },
        "schema_viability": flags,
        "response_boundary": {
            "header_lines_read": 1,
            "data_rows_read": 0,
            "response_rows_read": 0,
            "species_values_read": 0,
            "timestamp_values_read": 0,
            "count_values_read": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    value = precheck(args.csv, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
