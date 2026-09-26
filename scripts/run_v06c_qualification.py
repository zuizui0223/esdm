#!/usr/bin/env python3
"""Run frozen pre-MCMC v0.6c qualification."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess


FROZEN_GATE_COMMIT = "cd1088f1d60f771b4ab6d00d089c7a9f0b08150f"
FROZEN_GATE_BLOB_SHA = "f5fb2ae16ec8c0b37eeb1a9d87f688763ce18d83"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V06C_BUDGET_MATCHED_ACCESSIBILITY_GATE.md"
)
MAX_BUDGET_ERROR = 1e-12
MAX_ACCESS_SD_RATIO = 0.50


def _parser():
    parser = argparse.ArgumentParser(description="Run frozen v0.6c qualification.")
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload
    ).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("v0.6c gate blob mismatch")
    return observed


def _git_sha():
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _json_safe(value):
    if is_dataclass(value):
        return {
            field.name: _json_safe(getattr(value, field.name))
            for field in fields(value)
        }
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
    from esdm.validate.v06c_fixture import V06C_ACCESS_TARGETS
    from esdm.validate.v06c_qualification import evaluate_v06c_qualification

    args = _parser().parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema": "esdm.v06c.qualification.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")

    try:
        observed = _verify_gate()
        q = evaluate_v06c_qualification()
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "qualification",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
        return 2

    passed = (
        q.relative_budget_error <= MAX_BUDGET_ERROR
        and q.direct_all_structural
        and q.direct_all_practical
        and q.matched_all_structural
        and all(
            q.access_sd_proxy_ratios[target] <= MAX_ACCESS_SD_RATIO
            for target in V06C_ACCESS_TARGETS
        )
    )
    payload = {
        **base,
        "status": "PASS" if passed else "FAIL",
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed,
        "qualification": _json_safe(q),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
