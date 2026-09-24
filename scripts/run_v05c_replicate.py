#!/usr/bin/env python3
"""Run one frozen v0.5c event-gated claim replicate."""

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


FROZEN_GATE_COMMIT = "884872d28bc848539836e13e9f357b82f3794d01"
FROZEN_GATE_BLOB_SHA = "c5446065cc81ea27a6c59861a3ae52a1437e8909"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V05C_EVENT_GATED_CLAIM_GATE.md"
)
FROZEN_WORLDS = ("interaction_event", "hidden_driver_null")
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20261009
FROZEN_SEED_STRIDE = 83
FROZEN_NULL_OFFSET = 1000000
FROZEN_WARMUP = 300
FROZEN_SAMPLES = 350
FROZEN_CHAINS = 2
FROZEN_CREDIBLE_MASS = 0.90
FROZEN_TARGET_ACCEPT = 0.90


def _parser():
    parser = argparse.ArgumentParser(
        description="Run one frozen v0.5c event-gated replicate."
    )
    parser.add_argument("--world", choices=FROZEN_WORLDS, required=True)
    parser.add_argument("--replicate", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--progress-bar", action="store_true")
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload
    ).hexdigest()


def _verify_gate():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError(
            f"v0.5c gate blob mismatch: expected {FROZEN_GATE_BLOB_SHA}, "
            f"observed {observed}"
        )
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
    if world not in FROZEN_WORLDS:
        raise ValueError("unknown frozen v0.5c world")
    index = int(replicate)
    if not 0 <= index < FROZEN_REPLICATES:
        raise ValueError("replicate outside frozen v0.5c range")
    offset = 0 if world == "interaction_event" else FROZEN_NULL_OFFSET
    return FROZEN_BASE_SEED + offset + FROZEN_SEED_STRIDE * index


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
    from esdm.validate.v05c_run import run_v05c_replicate

    args = _parser().parse_args()
    seed = _seed(args.world, args.replicate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        observed_gate = _verify_gate()
        row = run_v05c_replicate(
            world=args.world,
            replicate=args.replicate,
            seed=seed,
            num_warmup=FROZEN_WARMUP,
            num_samples=FROZEN_SAMPLES,
            num_chains=FROZEN_CHAINS,
            credible_mass=FROZEN_CREDIBLE_MASS,
            progress_bar=bool(args.progress_bar),
            target_accept_prob=FROZEN_TARGET_ACCEPT,
        )
    except Exception as exc:
        payload = {
            "schema": "esdm.v05c.shard.v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "git_sha": _git_sha(),
            "gate_freeze_commit": FROZEN_GATE_COMMIT,
            "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
            "world": args.world,
            "replicate_index": int(args.replicate),
            "seed": seed,
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
        return 2

    payload = {
        "schema": "esdm.v05c.shard.v1",
        "status": "COMPLETE",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "observed_gate_blob_sha": observed_gate,
        "world": args.world,
        "replicate_index": int(args.replicate),
        "seed": seed,
        "record": _json_safe(row),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
