#!/usr/bin/env python3
"""Run the frozen deterministic v0.6b joint-only identification audit."""

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


FROZEN_GATE_COMMIT = "a4cd5f2ac809fd4db65ce4418f0648a55978fd59"
FROZEN_GATE_BLOB_SHA = "31d121519fe018c4cc20d75bfbfadbecc932f7a7"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V06B_JOINT_IDENTIFICATION_AUDIT.md"
)


def _parser():
    parser = argparse.ArgumentParser(description="Run frozen v0.6b joint-only audit.")
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload
    ).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("v0.6b gate blob mismatch")
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
    from esdm.validate.v06b_joint_audit import evaluate_v06b_joint_audit

    args = _parser().parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema": "esdm.v06b.joint_identification_audit.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")

    try:
        observed = _verify_gate()
        audit = evaluate_v06b_joint_audit()
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "audit",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
        return 2

    if not audit.intercept_only_refused:
        status = "FAIL_CONTROL"
        interpretation = "intercept_only_refusal_failed"
        exit_code = 1
    elif audit.structured_all_structural and audit.structured_all_practical:
        status = "COMPLETE"
        interpretation = "A_all_structural_and_practical"
        exit_code = 0
    elif audit.structured_all_structural:
        status = "COMPLETE"
        interpretation = "B_structural_but_practically_weak"
        exit_code = 0
    else:
        status = "COMPLETE"
        interpretation = "C_structural_refusal_remains"
        exit_code = 0

    payload = {
        **base,
        "status": status,
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed,
        "interpretation": interpretation,
        "audit": _json_safe(audit),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
