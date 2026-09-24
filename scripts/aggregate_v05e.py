#!/usr/bin/env python3
"""Aggregate frozen v0.5e evidence-separation shards."""

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


FROZEN_GATE_COMMIT = "8d3ffa928dcb6ff9c36a8b10eaa1c76028eaecf0"
FROZEN_GATE_BLOB_SHA = "c9dde4bf7ef95541fdcf183d1755b7c0a05c208b"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V05E_EVIDENCE_SEPARATION_GATE.md"
)
FROZEN_WORLDS = (
    "hidden_event_silent",
    "realized_only",
    "directed_realized",
)
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20261009
FROZEN_SEED_STRIDE = 83
FROZEN_WORLD_OFFSETS = {
    "hidden_event_silent": 0,
    "realized_only": 1000000,
    "directed_realized": 2000000,
}


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.5e shards.")
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("v0.5e gate blob mismatch")
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


def _seed(world: str, replicate: int) -> int:
    return (
        FROZEN_BASE_SEED
        + FROZEN_WORLD_OFFSETS[world]
        + FROZEN_SEED_STRIDE * int(replicate)
    )


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
    from esdm.validate.v05e_gate import evaluate_v05e_gate
    from esdm.validate.v05e_run import V05EReplicate, summarize_v05e

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v05e.evidence_separation.v1",
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
        expected_count = len(FROZEN_WORLDS) * FROZEN_REPLICATES
        if len(paths) != expected_count:
            raise RuntimeError(
                f"expected {expected_count} shards, found {len(paths)}"
            )
        shards = [json.loads(path.read_text()) for path in paths]
        keyed = {
            (row["world"], int(row["replicate_index"])): row
            for row in shards
        }
        expected = {
            (world, replicate)
            for world in FROZEN_WORLDS
            for replicate in range(FROZEN_REPLICATES)
        }
        if set(keyed) != expected:
            raise RuntimeError("v0.5e shard identities are incomplete or duplicated")

        records = []
        for world in FROZEN_WORLDS:
            for replicate in range(FROZEN_REPLICATES):
                shard = keyed[(world, replicate)]
                if shard.get("status") != "COMPLETE":
                    raise RuntimeError(f"shard {world}/{replicate} not COMPLETE")
                if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                    raise RuntimeError("shard gate commit mismatch")
                if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                    raise RuntimeError("shard gate blob mismatch")
                if int(shard["seed"]) != _seed(world, replicate):
                    raise RuntimeError(f"shard seed mismatch: {world}/{replicate}")
                records.append(V05EReplicate(**shard["record"]))

        summary = summarize_v05e(records)
        decision = evaluate_v05e_gate(summary)
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
        "summary": _json_safe(summary),
        "gate": _json_safe(decision),
        "replicates": [_json_safe(row) for row in records],
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
