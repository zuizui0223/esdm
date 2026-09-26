#!/usr/bin/env python3
"""Aggregate all frozen v0.4-R5b replicate shards and apply the gate."""

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


FROZEN_GATE_COMMIT = "98c828797e73d6b40cf9a73651662d7877473bbc"
FROZEN_GATE_BLOB_SHA = "227938d2b104d6e900dbbc7ca9d82d019db9f526"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "validation" / "V04_R5B_OUTCOME_GATE.md"
)
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20260926
FROZEN_SEED_STRIDE = 47
FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser():
    parser = argparse.ArgumentParser(description="Aggregate frozen R5b shards.")
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _verify_gate_blob() -> str:
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError(
            f"R5b gate blob mismatch: expected {FROZEN_GATE_BLOB_SHA}, observed {observed}"
        )
    return observed


def _git_sha() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def _replicate_seed(index: int) -> int:
    return FROZEN_BASE_SEED + int(index) * FROZEN_SEED_STRIDE


def _fetch_source():
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v04-r5b-aggregate"},
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


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    from esdm.validate.v04_r2_run import V04R2Replicate, _extrapolation_integrity, summarize_v04_r2
    from esdm.validate.v04_r5a_design import build_v04_r5a_fixture
    from esdm.validate.v04_r5a_gate import (
        evaluate_v04_r5a_identification,
        qualification_summary,
    )
    from esdm.validate.v04_r5b_gate import evaluate_v04_r5b_gate

    args = _parser().parse_args()
    output = Path(args.output)
    base = {
        "schema": "esdm.v04_r5b.outcome.v1",
        "status": "INFRASTRUCTURE_BLOCKED",
        "git_sha": _git_sha(),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
    }
    _write(output, base)

    try:
        observed_gate = _verify_gate_blob()
        source_bytes, source_audit = _fetch_source()
        source_text = source_bytes.decode("utf-8")
        paths = sorted(Path(args.shard_dir).rglob("*.json"))
        if len(paths) != FROZEN_REPLICATES:
            raise RuntimeError(
                f"expected {FROZEN_REPLICATES} shard JSON files, found {len(paths)}"
            )
        shards = [json.loads(path.read_text()) for path in paths]
        by_index = {int(row["replicate_index"]): row for row in shards}
        if set(by_index) != set(range(FROZEN_REPLICATES)):
            raise RuntimeError("R5b shard replicate identities are incomplete or duplicated")

        records = []
        for index in range(FROZEN_REPLICATES):
            shard = by_index[index]
            if shard.get("status") != "COMPLETE":
                raise RuntimeError(f"R5b shard {index} is not COMPLETE")
            if shard.get("gate_freeze_commit") != FROZEN_GATE_COMMIT:
                raise RuntimeError("R5b shard gate commit mismatch")
            if shard.get("gate_blob_sha") != FROZEN_GATE_BLOB_SHA:
                raise RuntimeError("R5b shard gate blob mismatch")
            if int(shard["seed"]) != _replicate_seed(index):
                raise RuntimeError(f"R5b shard {index} seed mismatch")
            if shard["source_audit"]["observed_git_blob_sha1"] != FROZEN_SOURCE_BLOB_SHA:
                raise RuntimeError(f"R5b shard {index} source mismatch")
            record = dict(shard["record"])
            record["replicate"] = index
            records.append(V04R2Replicate(**record))

        identification = evaluate_v04_r5a_identification(source_text)
        qualification = qualification_summary(source_text, identification)
        fixture = build_v04_r5a_fixture(source_text)
        outcome = summarize_v04_r2(
            tuple(records),
            identification=identification,
            extrapolation_integrity=_extrapolation_integrity(fixture),
        )
        decision = evaluate_v04_r5b_gate(qualification, outcome)
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
        "qualification": _json_safe(qualification),
        "outcome_summary": _json_safe(outcome),
        "gate": _json_safe(decision),
        "replicates": [
            _json_safe(row)
            | {"activity_gain": row.activity_gain, "state_gain": row.state_gain}
            for row in records
        ],
    }
    _write(output, payload)
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
