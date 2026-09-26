#!/usr/bin/env python3
"""Read exactly the Snapshot Japan sequences CSV physical header."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_JAPAN_SEQUENCE_HEADER_CONTRACT.json"
OUTPUT = ROOT / "artifacts" / "snapshot_japan_sequence_header.json"


def _read_first_line(url: str, *, max_bytes: int, user_agent: str):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    opened = bytearray()
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        status = int(getattr(response, "status", 200))
        final_url = response.geturl()
        while len(opened) < max_bytes:
            value = response.read(1)
            if not value:
                break
            opened.extend(value)
            if value == b"\n":
                break
    if status != 200:
        raise RuntimeError(f"sequence header GET returned HTTP {status}")
    if not opened:
        raise RuntimeError("empty response while reading sequence header")
    if b"\n" not in opened:
        raise RuntimeError("sequence header exceeded frozen byte ceiling")

    raw = bytes(opened)
    line = raw[:-1]
    terminator = "LF"
    if line.endswith(b"\r"):
        line = line[:-1]
        terminator = "CRLF"
    text = line.decode("utf-8-sig")
    columns = tuple(next(csv.reader(io.StringIO(text))))
    return raw, columns, terminator, final_url


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    expected = tuple(contract["expected_header"])
    output = OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)

    base = {
        "schema": "esdm.empirical_r5b.snapshot_japan_sequence_header_result.v1",
        "status": "STOP_PRE_RESPONSE_HEADER_TRANSPORT_OR_SCHEMA",
        "response_rows_opened": 0,
        "response_values_opened": False,
        "species_values_opened": False,
        "age_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0
    }
    try:
        raw, columns, terminator, final_url = _read_first_line(
            contract["publisher_metadata"]["original_file_url"],
            max_bytes=int(contract["header_transport"]["max_header_bytes"]),
            user_agent=contract["header_transport"]["user_agent"],
        )
        if columns != expected:
            raise RuntimeError(
                "physical sequence header does not match publisher-frozen schema"
            )
        result = {
            **base,
            "status": "HEADER_QUALIFIED",
            "header_bytes_opened": len(raw),
            "header_line_terminator": terminator,
            "header_sha256": hashlib.sha256(raw).hexdigest(),
            "column_count": len(columns),
            "columns": list(columns),
            "final_url": final_url,
            "next_gate": "freeze full empirical response/model contract before any data-row access"
        }
    except Exception as exc:
        result = {
            **base,
            "header_bytes_opened": 0,
            "reason": f"{type(exc).__name__}: {exc}"
        }

    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
