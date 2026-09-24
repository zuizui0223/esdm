#!/usr/bin/env python3
"""Run one frozen v0.7b dynamic recovery/transfer replicate."""
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


FROZEN_GATE_COMMIT = "7c454d78c61c259504fa3a621eb65caf954c058a"
FROZEN_GATE_BLOB_SHA = "14e02c13b1314d6ca3d91491dd799f0b1b85cf4a"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V07B_DYNAMIC_RECOVERY_TRANSFER_GATE.md"
)
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20261029
FROZEN_SEED_STRIDE = 109
FROZEN_WARMUP = 300
FROZEN_SAMPLES = 350
FROZEN_CHAINS = 2
FROZEN_CREDIBLE_MASS = 0.90
FROZEN_TARGET_ACCEPT = 0.90


def _parser():
    parser = argparse.ArgumentParser(description="Run one frozen v0.7b replicate.")
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
    value = int(index)
    if not 0 <= value < FROZEN_REPLICATES:
        raise ValueError("replicate outside frozen v0.7b range")
    return FROZEN_BASE_SEED + FROZEN_SEED_STRIDE * value


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
    from esdm.validate.v07b_run import run_v07b_replicate

    args = _parser().parse_args()
    seed = _seed(args.replicate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        observed_gate = _verify_gate()
        row = run_v07b_replicate(
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
            "schema": "esdm.v07b.shard.v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "git_sha": _git_sha(),
            "gate_freeze_commit": FROZEN_GATE_COMMIT,
            "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
            "replicate_index": int(args.replicate),
            "seed": seed,
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 2

    payload = {
        "schema": "esdm.v07b.shard.v1",
        "status": "COMPLETE",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "observed_gate_blob_sha": observed_gate,
        "replicate_index": int(args.replicate),
        "seed": seed,
        "record": _json_safe(row),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
