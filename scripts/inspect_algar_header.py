#!/usr/bin/env python3
"""Open only the physical header of the frozen Algar empirical candidate."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "ALGAR_HEADER_CONTRACT.json"


def _read_header_only(url: str, *, user_agent: str, max_bytes: int):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept-Encoding": "identity"},
        method="GET",
    )
    opened = bytearray()
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        while len(opened) < max_bytes:
            chunk = response.read(1)
            if not chunk:
                break
            opened.extend(chunk)
            if chunk == b"\n":
                break
    if not opened:
        raise RuntimeError("empty response while reading Algar header")
    if b"\n" not in opened:
        raise RuntimeError("Algar header exceeded frozen byte ceiling")
    header_bytes = bytes(opened)
    before_lf = header_bytes.split(b"\n", 1)[0]
    if before_lf.endswith(b"\r"):
        before_lf = before_lf[:-1]
        terminator = "CRLF"
    else:
        terminator = "LF"
    header_text = before_lf.decode("utf-8-sig")
    columns = next(csv.reader(io.StringIO(header_text)))
    if not columns or any(not str(value).strip() for value in columns):
        raise RuntimeError("Algar header contains empty column names")
    if len(columns) != len(set(columns)):
        raise RuntimeError("Algar header contains duplicate column names")
    return header_bytes, tuple(columns), terminator


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    output = ROOT / "artifacts" / "algar_header_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    base = {
        "schema": "esdm.empirical_r5b.algar_header_result.v1",
        "status": "STOP_PRE_RESPONSE_HEADER_TRANSPORT",
        "dataset_doi": contract["dataset"]["doi"],
        "file_name": contract["dataset"]["candidate_file_name"],
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        payload, columns, terminator = _read_header_only(
            contract["dataset"]["download_url"],
            user_agent=contract["header_transport"]["user_agent"],
            max_bytes=int(contract["header_transport"]["max_header_bytes"]),
        )
        result = {
            **base,
            "status": "HEADER_CAPTURED_FOR_BINDING",
            "header_bytes_opened": len(payload),
            "header_line_terminator": terminator,
            "header_sha256": hashlib.sha256(payload).hexdigest(),
            "columns": list(columns),
            "column_count": len(columns),
        }
    except Exception as exc:
        result = {
            **base,
            "reason": f"{type(exc).__name__}: {exc}",
            "header_bytes_opened": 0,
        }

    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
