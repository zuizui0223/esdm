#!/usr/bin/env python3
"""Aggregate frozen v0.7b recovery/transfer shards."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


FROZEN_GATE_COMMIT = "7c454d78c61c259504fa3a621eb65caf954c058a"
FROZEN_GATE_BLOB_SHA = "14e02c13b1314d6ca3d91491dd799f0b1b85cf4a"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V07B_DYNAMIC_RECOVERY_TRANSFER_GATE.md"
)
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20261029
FROZEN_SEED_STRIDE = 109


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.7b shards.")
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
        raise RuntimeError("v0.7b gate blob mismatch")
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
    from esdm.validate.v07b_gate import evaluate_v07b_gate
    from esdm.validate.v07b_qualification import evaluate_v07b_identification
    from esdm.validate.v07b_run import V07BReplicate, summarize_v07b

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v07b.dynamic_transfer.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "information_filtration": [
            {
                "name": "suitability_only",
                "information": ["suitability"],
                "score_field": "occupancy_knockout_heldout_log_score",
            },
            {
                "name": "suitability_dynamic_occupancy",
                "information": ["suitability", "dynamic_occupancy"],
                "score_field": "full_heldout_log_score",
            },
        ],
        "score_contract": {
            "kind": "log",
            "name": "mean_heldout_log_predictive_density",
            "unit": "nats_per_heldout_context",
            "orientation": "higher_is_better",
        },
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
            raise RuntimeError("v0.7b shard identities incomplete or duplicated")

        rows = []
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
            record = V07BReplicate(**shard["record"])
            if not math.isfinite(record.full_heldout_log_score):
                raise RuntimeError("full absolute heldout score is non-finite")
            if not math.isfinite(record.occupancy_knockout_heldout_log_score):
                raise RuntimeError("knockout absolute heldout score is non-finite")
            rows.append(record)

        qualification = evaluate_v07b_identification()
        summary = summarize_v07b(rows)
        decision = evaluate_v07b_gate(qualification, summary)
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
        "replicates": [_json_safe(row) for row in rows],
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
