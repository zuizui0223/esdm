#!/usr/bin/env python3
"""Aggregate frozen v0.7l selective-adaptation shards."""
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


FROZEN_GATE_COMMIT = "363318c3c30aa9ff37b3d39153ecc8ab3100a14a"
FROZEN_GATE_BLOB_SHA = "62f2183328ab7abcf6d727573031b149bfacebd3"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V07L_SELECTIVE_ADAPTATION_GATE.md"
)
FROZEN_WORLDS = (
    "strong_headroom",
    "threshold_below",
    "threshold_above",
    "negligible_headroom",
)
FROZEN_REPLICATES_PER_WORLD = 16
FROZEN_PILOT_BASE_SEEDS = {
    "strong_headroom": 20280131,
    "threshold_below": 20290131,
    "threshold_above": 20300131,
    "negligible_headroom": 20310131,
}
FROZEN_CONFIRM_BASE_SEEDS = {
    "strong_headroom": 20280231,
    "threshold_below": 20290231,
    "threshold_above": 20300231,
    "negligible_headroom": 20310231,
}
FROZEN_SEED_STRIDE = 193


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.7l shards.")
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
        raise RuntimeError("v0.7l gate blob mismatch")
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


def _seeds(world: str, index: int):
    name = str(world)
    value = int(index)
    return (
        FROZEN_PILOT_BASE_SEEDS[name] + FROZEN_SEED_STRIDE * value,
        FROZEN_CONFIRM_BASE_SEEDS[name] + FROZEN_SEED_STRIDE * value,
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
    from esdm.validate.v07l_gate import evaluate_v07l_gate
    from esdm.validate.v07l_run import V07LReplicate, summarize_v07l

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v07l.selective_adaptation.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "trigger_ratio": 0.80,
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate()
        paths = sorted(Path(args.shard_dir).rglob("*.json"))
        expected = len(FROZEN_WORLDS) * FROZEN_REPLICATES_PER_WORLD
        if len(paths) != expected:
            raise RuntimeError(f"expected {expected} shards, found {len(paths)}")
        shards = [json.loads(path.read_text()) for path in paths]
        keyed = {
            (str(row["world"]), int(row["replicate_index"])): row
            for row in shards
        }
        expected_keys = {
            (world, replicate)
            for world in FROZEN_WORLDS
            for replicate in range(FROZEN_REPLICATES_PER_WORLD)
        }
        if set(keyed) != expected_keys:
            raise RuntimeError("v0.7l shard identities are incomplete or duplicated")

        records = []
        for world in FROZEN_WORLDS:
            for replicate in range(FROZEN_REPLICATES_PER_WORLD):
                shard = keyed[(world, replicate)]
                if shard.get("status") != "COMPLETE":
                    raise RuntimeError(f"shard {world}:{replicate} not COMPLETE")
                if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                    raise RuntimeError("shard gate commit mismatch")
                if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                    raise RuntimeError("shard gate blob mismatch")
                pilot_seed, confirm_seed = _seeds(world, replicate)
                if int(shard["pilot_seed"]) != pilot_seed:
                    raise RuntimeError(f"pilot seed mismatch: {world}:{replicate}")
                if int(shard["confirm_seed"]) != confirm_seed:
                    raise RuntimeError(f"confirm seed mismatch: {world}:{replicate}")
                record = V07LReplicate(**shard["record"])
                if record.pilot_seed != pilot_seed or record.confirm_seed != confirm_seed:
                    raise RuntimeError(f"record seed mismatch: {world}:{replicate}")
                records.append(record)

        summary = summarize_v07l(records)
        decision = evaluate_v07l_gate(summary)
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
