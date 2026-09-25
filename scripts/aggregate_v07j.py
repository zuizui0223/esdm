#!/usr/bin/env python3
"""Aggregate frozen v0.7j shifted-population robustness shards."""
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


FROZEN_GATE_COMMIT = "14dfe742bd1f676ffa1cd94ea99ee9f5f9e0d5c7"
FROZEN_GATE_BLOB_SHA = "ef2c8f6aa412a3a05a1201778ff430d4d4385613"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V07J_POPULATION_SHIFT_GATE.md"
)
FROZEN_REPLICATES_PER_WORLD = 12
FROZEN_SEED_FAMILIES = {
    "low_occupancy": (20300117, 211),
    "high_occupancy": (20310117, 223),
    "high_turnover": (20320117, 227),
}


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.7j shards.")
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
        raise RuntimeError("v0.7j gate blob mismatch")
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


def _seed(world: str, replicate: int) -> int:
    base, stride = FROZEN_SEED_FAMILIES[world]
    return int(base + stride * int(replicate))


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
    from esdm.validate.v07j_fixture import V07J_WORLD_ORDER
    from esdm.validate.v07j_gate import evaluate_v07j_gate
    from esdm.validate.v07j_run import V07JReplicate, summarize_v07j

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v07j.population_shift.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "source_schedule": [2, 6, 7, 8],
        "baseline_schedule": [1, 2, 3, 4],
        "odsp_transfer_source": False,
        "reason_not_odsp_transfer": (
            "selected and baseline are alternative observation schedules for the "
            "same dynamic-occupancy information, not nested information levels"
        ),
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate()
        paths = sorted(Path(args.shard_dir).rglob("*.json"))
        expected = FROZEN_REPLICATES_PER_WORLD * len(V07J_WORLD_ORDER)
        if len(paths) != expected:
            raise RuntimeError(f"expected {expected} shards, found {len(paths)}")
        shards = [json.loads(path.read_text()) for path in paths]
        keyed = {
            (str(row["world"]), int(row["replicate_index"])): row
            for row in shards
        }
        expected_keys = {
            (world, replicate)
            for world in V07J_WORLD_ORDER
            for replicate in range(FROZEN_REPLICATES_PER_WORLD)
        }
        if set(keyed) != expected_keys:
            raise RuntimeError("v0.7j shard identities incomplete or duplicated")

        records = []
        for world in V07J_WORLD_ORDER:
            for replicate in range(FROZEN_REPLICATES_PER_WORLD):
                shard = keyed[(world, replicate)]
                if shard.get("status") != "COMPLETE":
                    raise RuntimeError(f"shard {(world, replicate)} not COMPLETE")
                if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                    raise RuntimeError("shard gate commit mismatch")
                if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                    raise RuntimeError("shard gate blob mismatch")
                if int(shard["seed"]) != _seed(world, replicate):
                    raise RuntimeError(f"shard seed mismatch: {(world, replicate)}")
                records.append(V07JReplicate(**shard["record"]))

        summary = summarize_v07j(records)
        decision = evaluate_v07j_gate(summary)
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
