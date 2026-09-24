#!/usr/bin/env python3
"""Run the frozen v0.5a identification-only qualification gate."""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
from collections.abc import Mapping


FROZEN_GATE_COMMIT = "d5f8d3e10c059cedfb8c3efbf5a1d232efa3507d"
FROZEN_GATE_BLOB_SHA = "c5d43c4baa01d631704e6769db8eed49ec85837b"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V05A_IDENTIFICATION_GATE.md"
)

FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Frozen v0.5a identification qualification. "
            "Scientific thresholds and worlds are not configurable."
        )
    )
    parser.add_argument(
        "--output",
        default="v05a_identification_qualification.json",
        help="audit JSON output path",
    )
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate_blob() -> str:
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError(
            f"v0.5a gate blob mismatch: expected {FROZEN_GATE_BLOB_SHA}, observed {observed}"
        )
    return observed


def _git_sha():
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def _fetch_source():
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v05a-identification"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    observed = _git_blob_sha1(payload)
    if observed != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError("pinned source blob mismatch")
    return payload, {
        "commit": FROZEN_SOURCE_COMMIT,
        "path": FROZEN_SOURCE_PATH,
        "expected_git_blob_sha1": FROZEN_SOURCE_BLOB_SHA,
        "observed_git_blob_sha1": observed,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _json_safe(value):
    if is_dataclass(value):
        return {field.name: _json_safe(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "value"):
        return _json_safe(value.value)
    return value


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    from esdm.validate.v05a_gate import (
        evaluate_v05a_identification,
        evaluate_v05a_identification_gate,
    )

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v05a.identification_qualification.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "infrastructure_block": {
            "stage": "start",
            "reason": "qualification has not completed",
        },
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate_blob()
        source_bytes, source_audit = _fetch_source()
        identification = evaluate_v05a_identification(
            source_bytes.decode("utf-8")
        )
        decision = evaluate_v05a_identification_gate(identification)
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "qualification",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        _write(output, base)
        return 2

    payload = {
        **base,
        "status": "PASS" if decision.passed else "FAIL",
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed_gate,
        "source_audit": source_audit,
        "identification": _json_safe(identification),
        "gate": _json_safe(decision),
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
