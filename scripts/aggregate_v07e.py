#!/usr/bin/env python3
"""Aggregate frozen v0.7e reciprocal static-world shards."""
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


FROZEN_GATE_COMMIT = "a047fdb0fd7843b83169d5b168d86de005143c3b"
FROZEN_GATE_BLOB_SHA = "e089e43ff009d11e87a16cd7f1c18276b0017f41"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V07E_RECIPROCAL_STATIC_WORLD_GATE.md"
)
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20261217
FROZEN_SEED_STRIDE = 173


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.7e shards.")
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload
    ).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("v0.7e gate blob mismatch")
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


def _seed(index: int) -> int:
    return FROZEN_BASE_SEED + FROZEN_SEED_STRIDE * int(index)


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


def _write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    from esdm.validate.v07e_gate import evaluate_v07e_gate
    from esdm.validate.v07e_qualification import evaluate_v07e_identification
    from esdm.validate.v07e_run import V07EReplicate, summarize_v07e

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v07e.reciprocal_static.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate()
        paths = sorted(Path(args.shard_dir).rglob("*.json"))
        if len(paths) != FROZEN_REPLICATES:
            raise RuntimeError(
                f"expected {FROZEN_REPLICATES} shards, found {len(paths)}"
            )
        shards = [json.loads(path.read_text()) for path in paths]
        keyed = {int(row["replicate_index"]): row for row in shards}
        if set(keyed) != set(range(FROZEN_REPLICATES)):
            raise RuntimeError("v0.7e shard identities incomplete or duplicated")

        records = []
        for replicate in range(FROZEN_REPLICATES):
            shard = keyed[replicate]
            if shard.get("status") != "COMPLETE":
                raise RuntimeError(f"shard {replicate} not COMPLETE")
            if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                raise RuntimeError("shard gate commit mismatch")
            if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                raise RuntimeError("shard gate blob mismatch")
            if int(shard["seed"]) != _seed(replicate):
                raise RuntimeError(f"shard seed mismatch: {replicate}")
            records.append(V07EReplicate(**shard["record"]))

        qualification = evaluate_v07e_identification()
        summary = summarize_v07e(records)
        decision = evaluate_v07e_gate(qualification, summary)
    except Exception as exc:
        base["infrastructure_block"] = {
            "stage": "aggregate",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        _write(output, base)
        return 2

    payload = {
        **base,
        "status": "PASS" if decision.passed else "FAIL",
        "infrastructure_block": None,
        "observed_gate_blob_sha": observed_gate,
        "qualification": _json_safe(qualification),
        "summary": _json_safe(summary),
        "gate": _json_safe(decision),
        "replicates": [_json_safe(row) for row in records],
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
