#!/usr/bin/env python3
"""Aggregate frozen v0.5f interaction-transfer replication shards."""
from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from collections.abc import Mapping


FROZEN_GATE_COMMIT = "2247728b88c1b0acce7cf4f8362bb9d5cd541092"
FROZEN_GATE_BLOB_SHA = "f94a598acaef95ca3d3387b8aedfed9d0dd73dd9"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V05F_INTERACTION_TRANSFER_REPLICATION_GATE.md"
)
FROZEN_WORLDS = ("interaction", "measured_shared_null")
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20271001
FROZEN_SEED_STRIDE = 73
FROZEN_NULL_OFFSET = 1000000


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen v0.5f shards.")
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError("v0.5f gate blob mismatch")
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
    offset = 0 if world == "interaction" else FROZEN_NULL_OFFSET
    return FROZEN_BASE_SEED + offset + FROZEN_SEED_STRIDE * int(replicate)


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
    from esdm.validate.v05a_qualification import evaluate_v05a_identification
    from esdm.validate.v05f_gate import evaluate_v05f_gate
    from esdm.validate.v05f_run import V05FReplicate, summarize_v05f

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v05f.interaction_transfer_replication.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "replication_of": "esdm.v05a.directed_known_truth.v1",
        "information_filtration": [
            {
                "name": "measured_environment",
                "information": ["measured_environment"],
                "score_field": "partner_knockout_heldout_log_score",
            },
            {
                "name": "measured_environment_directed_partner",
                "information": ["measured_environment", "directed_partner_latent"],
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
            raise RuntimeError("v0.5f shard identities are incomplete or duplicated")

        records = []
        for world, replicate in sorted(expected):
            shard = keyed[(world, replicate)]
            if shard.get("status") != "COMPLETE":
                raise RuntimeError(f"shard {world}/{replicate} not COMPLETE")
            if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                raise RuntimeError("shard gate commit mismatch")
            if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                raise RuntimeError("shard gate blob mismatch")
            if int(shard["seed"]) != _seed(world, replicate):
                raise RuntimeError(f"shard seed mismatch: {world}/{replicate}")
            record = V05FReplicate(**shard["record"])
            if not math.isfinite(record.full_heldout_log_score):
                raise RuntimeError("full absolute heldout score is non-finite")
            if not math.isfinite(record.partner_knockout_heldout_log_score):
                raise RuntimeError("knockout absolute heldout score is non-finite")
            records.append(record)

        qualification = evaluate_v05a_identification()
        summary = summarize_v05f(records)
        decision = evaluate_v05f_gate(qualification, summary)
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
