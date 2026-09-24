#!/usr/bin/env python3
"""Run one frozen v0.4-R7 paired calibration replicate."""

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


FROZEN_GATE_COMMIT = "2c6c1473cbe7a571ee8972476225574a7906a1cb"
FROZEN_GATE_BLOB_SHA = "7c3261211cc8b1eb51e50f912457dd54dd8fdb33"
GATE_PATH = Path(__file__).resolve().parents[1] / "docs" / "validation" / "V04_R7_BUDGET_MATCHED_GATE.md"

FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20260928
FROZEN_SEED_STRIDE = 67
FROZEN_WARMUP = 300
FROZEN_SAMPLES = 350
FROZEN_CHAINS = 2
FROZEN_TARGET_ACCEPT = 0.90

FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser():
    parser = argparse.ArgumentParser(description="Run one frozen R7 paired replicate.")
    parser.add_argument("--replicate", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--progress-bar", action="store_true")
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate_blob():
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError(
            f"R7 gate blob mismatch: expected {FROZEN_GATE_BLOB_SHA}, observed {observed}"
        )
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


def _seed(index: int) -> int:
    value = int(index)
    if not 0 <= value < FROZEN_REPLICATES:
        raise ValueError("replicate outside frozen R7 range")
    return FROZEN_BASE_SEED + value * FROZEN_SEED_STRIDE


def _fetch_source():
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v04-r7-shard"},
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


def main() -> int:
    from esdm.validate.v04_r7_run import run_v04_r7_replicate

    args = _parser().parse_args()
    seed = _seed(args.replicate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        observed_gate = _verify_gate_blob()
        source_bytes, source_audit = _fetch_source()
        row = run_v04_r7_replicate(
            source_bytes.decode("utf-8"),
            replicate=args.replicate,
            seed=seed,
            num_warmup=FROZEN_WARMUP,
            num_samples=FROZEN_SAMPLES,
            num_chains=FROZEN_CHAINS,
            progress_bar=bool(args.progress_bar),
            target_accept_prob=FROZEN_TARGET_ACCEPT,
        )
    except Exception as exc:
        payload = {
            "schema": "esdm.v04_r7.shard.v1",
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
        "schema": "esdm.v04_r7.shard.v1",
        "status": "COMPLETE",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "observed_gate_blob_sha": observed_gate,
        "source_audit": source_audit,
        "replicate_index": int(args.replicate),
        "seed": seed,
        "record": _json_safe(row)
        | {
            "heldout_gain": row.heldout_gain,
            "state_error_gain": row.state_error_gain,
        },
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
