#!/usr/bin/env python3
"""Aggregate all frozen v0.4-R6 matched-model shards."""

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


FROZEN_GATE_COMMIT = "3bae2166fdae6b568a0bb155d795e369445cadf1"
FROZEN_GATE_BLOB_SHA = "d6c15b922895aee40c072a1cab4c92781507c2e5"
GATE_PATH = Path(__file__).resolve().parents[1] / "docs" / "validation" / "V04_R6_MATCHED_GATE.md"

FROZEN_WORLDS = ("structured", "resolution_null")
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20260924
FROZEN_SEED_STRIDE = 61
FROZEN_NULL_OFFSET = 1000000
FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen R6 shards.")
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate_blob():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("R6 gate blob mismatch")
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
    offset = 0 if world == "structured" else FROZEN_NULL_OFFSET
    return FROZEN_BASE_SEED + offset + int(replicate) * FROZEN_SEED_STRIDE


def _fetch_source():
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v04-r6-aggregate"},
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


def _write(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    from esdm.validate.v04_r6_gate import evaluate_v04_r6_gate
    from esdm.validate.v04_r6_matched import V04R6Replicate, summarize_v04_r6

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v04_r6.matched.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate_blob()
        _source_bytes, source_audit = _fetch_source()
        paths = sorted(Path(args.shard_dir).rglob("*.json"))
        expected_count = len(FROZEN_WORLDS) * FROZEN_REPLICATES
        if len(paths) != expected_count:
            raise RuntimeError(f"expected {expected_count} shards, found {len(paths)}")
        shards = [json.loads(path.read_text()) for path in paths]
        keyed = {(row["world"], int(row["replicate_index"])): row for row in shards}
        expected = {
            (world, replicate)
            for world in FROZEN_WORLDS
            for replicate in range(FROZEN_REPLICATES)
        }
        if set(keyed) != expected:
            raise RuntimeError("R6 shard identities are incomplete or duplicated")

        records = []
        for world, replicate in sorted(expected):
            shard = keyed[(world, replicate)]
            if shard.get("status") != "COMPLETE":
                raise RuntimeError(f"R6 shard {world}/{replicate} not COMPLETE")
            if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                raise RuntimeError("R6 shard gate commit mismatch")
            if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                raise RuntimeError("R6 shard gate blob mismatch")
            if int(shard["seed"]) != _seed(world, replicate):
                raise RuntimeError(f"R6 shard seed mismatch: {world}/{replicate}")
            if shard["source_audit"]["observed_git_blob_sha1"] != FROZEN_SOURCE_BLOB_SHA:
                raise RuntimeError("R6 shard source mismatch")
            record = dict(shard["record"])
            record.pop("resolution_gain", None)
            records.append(V04R6Replicate(**record))

        summary = summarize_v04_r6(records)
        decision = evaluate_v04_r6_gate(summary)
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
        "source_audit": source_audit,
        "summary": _json_safe(summary),
        "gate": _json_safe(decision),
        "replicates": [
            _json_safe(row) | {"resolution_gain": row.resolution_gain}
            for row in records
        ],
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
