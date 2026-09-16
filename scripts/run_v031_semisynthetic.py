#!/usr/bin/env python3
"""Run the frozen v0.3.1 Gate F real-geometry semi-synthetic benchmark."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


FROZEN_REPLICATES = 20
FROZEN_BASE_SEED = 20260921
FROZEN_WARMUP = 200
FROZEN_SAMPLES = 250
FROZEN_CHAINS = 2
FROZEN_CREDIBLE_MASS = 0.90
FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser() -> argparse.ArgumentParser:
    description = (
        "Frozen v0.3.1 Gate F profile: "
        f"replicates={FROZEN_REPLICATES}, seed={FROZEN_BASE_SEED}, "
        f"warmup={FROZEN_WARMUP}, samples={FROZEN_SAMPLES}, chains={FROZEN_CHAINS}; "
        f"source={FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}. "
        "The scientific execution profile is intentionally not configurable."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        default="v031_semisynthetic_gate_f.json",
        help="JSON output path (default: v031_semisynthetic_gate_f.json)",
    )
    parser.add_argument(
        "--progress-bar",
        action="store_true",
        help="show NumPyro progress bars; does not change the frozen scientific profile",
    )
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _git_sha() -> str:
    from_env = os.environ.get("GITHUB_SHA")
    if from_env:
        return from_env
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def _fetch_source() -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v031-gate-f"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    observed_blob = _git_blob_sha1(payload)
    if observed_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "pinned source blob mismatch: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, observed {observed_blob}"
        )
    return payload, {
        "url": FROZEN_SOURCE_URL,
        "repository": "the-pudding/data",
        "commit": FROZEN_SOURCE_COMMIT,
        "path": FROZEN_SOURCE_PATH,
        "expected_git_blob_sha1": FROZEN_SOURCE_BLOB_SHA,
        "observed_git_blob_sha1": observed_blob,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def main() -> int:
    args = _parser().parse_args()

    from esdm.validate.v031_semisynthetic import V031_SEMISYNTHETIC_MANIFEST
    from esdm.validate.v031_semisynthetic_gate import (
        evaluate_v031_semisynthetic_gate,
        run_v031_semisynthetic_benchmark,
    )

    source_bytes, source_audit = _fetch_source()
    source_text = source_bytes.decode("utf-8")
    result = run_v031_semisynthetic_benchmark(
        source_text,
        replicates=FROZEN_REPLICATES,
        base_seed=FROZEN_BASE_SEED,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        credible_mass=FROZEN_CREDIBLE_MASS,
        progress_bar=bool(args.progress_bar),
    )
    decision = evaluate_v031_semisynthetic_gate(result.summary)

    payload = {
        "schema": "esdm.v031.gate_f.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "promotion_status": "NOT_READY",
        "promotion_note": (
            "Gate F is only one mandatory v0.3.1 gate; overall promotion requires A-F."
        ),
        "frozen_profile": {
            "replicates": FROZEN_REPLICATES,
            "base_seed": FROZEN_BASE_SEED,
            "num_warmup": FROZEN_WARMUP,
            "num_samples": FROZEN_SAMPLES,
            "num_chains": FROZEN_CHAINS,
            "credible_mass": FROZEN_CREDIBLE_MASS,
        },
        "source_audit": source_audit,
        "manifest": asdict(V031_SEMISYNTHETIC_MANIFEST),
        "train_space_count": result.train_space_count,
        "heldout_space_count": result.heldout_space_count,
        "heldout_block": result.heldout_block,
        "replicates": [asdict(row) | {"heldout_gain": row.heldout_gain} for row in result.replicates],
        "summary": asdict(result.summary),
        "gate_f": {
            "passed": decision.passed,
            "checks": [asdict(check) for check in decision.checks],
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "gate_f_passed": decision.passed,
                "promotion_status": payload["promotion_status"],
                "git_sha": payload["git_sha"],
                "source_sha256": source_audit["sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
