#!/usr/bin/env python3
"""Run the frozen deterministic v0.6c accessibility identification frontier."""

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


FROZEN_GATE_COMMIT = "1441d7ca241b09cad54563f3b6c0ed53bae6aa90"
FROZEN_GATE_BLOB_SHA = "f09f1857756bf1b14c2f8c9888f35cf1d6a44ab7"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V06C_ACCESSIBILITY_FRONTIER_GATE.md"
)


def _parser():
    parser = argparse.ArgumentParser(description="Run frozen v0.6c frontier.")
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


def _cell_summary(cell):
    def design_summary(rows):
        target_sd = {
            target: float(row.practical.target_sd_proxy)
            for target, row in rows.items()
        }
        statuses = {
            target: row.structural.status.value
            for target, row in rows.items()
        }
        weak = {
            target: bool(row.practical.weak)
            for target, row in rows.items()
        }
        first = next(iter(rows.values())).practical
        return {
            "structural_status": statuses,
            "practical_weak": weak,
            "target_sd_proxy": target_sd,
            "structural_identified_count": sum(
                value == "Identified" for value in statuses.values()
            ),
            "practical_pass_count": sum(not value for value in weak.values()),
            "relative_min_singular_value": float(
                first.relative_min_singular_value
            ),
            "condition_number": float(first.condition_number),
        }

    return {
        "geometry": cell.geometry,
        "access_intercept": cell.access_intercept,
        "joint_only": design_summary(cell.joint_only),
        "direct_calibrated": design_summary(cell.direct_calibrated),
    }


def main() -> int:
    from esdm.validate.v06c_frontier import evaluate_v06c_frontier

    args = _parser().parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema": "esdm.v06c.accessibility_frontier.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")

    try:
        observed = _verify_gate()
        frontier = evaluate_v06c_frontier()
        if not frontier.intercept_only_refused:
            raise RuntimeError("intercept-only hard invariant failed")
        if len(frontier.cells) != 9:
            raise RuntimeError("frozen frontier did not produce exactly 9 cells")
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "frontier",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
        return 2

    payload = {
        **base,
        "status": "COMPLETE",
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed,
        "intercept_only_refused": frontier.intercept_only_refused,
        "cells": [_cell_summary(cell) for cell in frontier.cells],
        "raw_frontier": _json_safe(frontier),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
