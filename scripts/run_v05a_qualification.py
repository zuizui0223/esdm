#!/usr/bin/env python3
"""Run the frozen pre-MCMC v0.5a interaction qualification."""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
from collections.abc import Mapping


FROZEN_GATE_COMMIT = "c6b7630030b63a950008191e4e4842950b660b6e"
FROZEN_GATE_BLOB_SHA = "d3c4d3f1b3f29858c8fdc2c69eb2003d5552111e"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V05A_DIRECTED_KNOWN_TRUTH_GATE.md"
)


def _parser():
    parser = argparse.ArgumentParser(description="Run frozen v0.5a identification qualification.")
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate():
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


def main() -> int:
    from esdm.validate.v05a_qualification import evaluate_v05a_identification

    args = _parser().parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema": "esdm.v05a.qualification.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")

    try:
        observed_gate = _verify_gate()
        qualification = evaluate_v05a_identification()
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "qualification",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
        return 2

    passed = all(
        (
            qualification.interaction_structural_pass,
            qualification.interaction_practical_pass,
            qualification.null_structural_pass,
            qualification.null_practical_pass,
        )
    )
    payload = {
        **base,
        "status": "PASS" if passed else "FAIL",
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed_gate,
        "qualification": _json_safe(qualification),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
