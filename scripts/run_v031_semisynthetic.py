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
import sys
import tempfile
import urllib.request


FROZEN_REPLICATES = 20
FROZEN_BASE_SEED = 20260921
FROZEN_SEED_STRIDE = 37
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
    parser.add_argument("--_worker-replicate", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--_worker-source", help=argparse.SUPPRESS)
    parser.add_argument("--_worker-output", help=argparse.SUPPRESS)
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


def _replicate_seed(replicate: int) -> int:
    index = int(replicate)
    if not 0 <= index < FROZEN_REPLICATES:
        raise ValueError(
            f"replicate index must be in [0, {FROZEN_REPLICATES - 1}], got {index}"
        )
    return FROZEN_BASE_SEED + index * FROZEN_SEED_STRIDE


def _worker_command(
    *,
    replicate: int,
    source_path: Path,
    output_path: Path,
    progress_bar: bool,
) -> list[str]:
    """Build one frozen worker command without exposing scientific controls."""

    index = int(replicate)
    _replicate_seed(index)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_worker-replicate",
        str(index),
        "--_worker-source",
        str(Path(source_path)),
        "--_worker-output",
        str(Path(output_path)),
    ]
    if progress_bar:
        command.append("--progress-bar")
    return command


def _read_worker_source(path: Path) -> bytes:
    payload = Path(path).read_bytes()
    observed_blob = _git_blob_sha1(payload)
    if observed_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "worker source blob mismatch: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, observed {observed_blob}"
        )
    return payload


def _run_worker(args: argparse.Namespace) -> int:
    if args._worker_source is None or args._worker_output is None:
        raise ValueError("Gate F worker requires internal source and output paths")

    from esdm.validate.v031_semisynthetic_gate import run_v031_semisynthetic_benchmark

    index = int(args._worker_replicate)
    seed = _replicate_seed(index)
    source_bytes = _read_worker_source(Path(args._worker_source))
    result = run_v031_semisynthetic_benchmark(
        source_bytes.decode("utf-8"),
        replicates=1,
        base_seed=seed,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        credible_mass=FROZEN_CREDIBLE_MASS,
        progress_bar=bool(args.progress_bar),
    )
    row = result.replicates[0]
    record = asdict(row)
    record["replicate"] = index
    payload = {
        "schema": "esdm.v031.gate_f.worker.v1",
        "replicate_index": index,
        "seed": seed,
        "record": record,
        "train_space_count": result.train_space_count,
        "heldout_space_count": result.heldout_space_count,
        "heldout_block": result.heldout_block,
    }
    output = Path(args._worker_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"replicate": index, "seed": seed, "worker_output": str(output)}, sort_keys=True))
    return 0


def _run_isolated_benchmark(
    source_bytes: bytes,
    *,
    progress_bar: bool,
):
    from esdm.validate.v031_semisynthetic_gate import (
        V031SemiSyntheticReplicate,
        V031SemiSyntheticResult,
        summarize_v031_semisynthetic,
    )

    records: list[V031SemiSyntheticReplicate] = []
    train_space_count: int | None = None
    heldout_space_count: int | None = None
    heldout_block: str | None = None

    with tempfile.TemporaryDirectory(prefix="esdm-v031-gate-f-") as tmp:
        workdir = Path(tmp)
        source_path = workdir / "pinned_source.csv"
        source_path.write_bytes(source_bytes)

        for replicate in range(FROZEN_REPLICATES):
            worker_output = workdir / f"replicate-{replicate:02d}.json"
            subprocess.run(
                _worker_command(
                    replicate=replicate,
                    source_path=source_path,
                    output_path=worker_output,
                    progress_bar=progress_bar,
                ),
                check=True,
            )
            payload = json.loads(worker_output.read_text(encoding="utf-8"))
            if int(payload["replicate_index"]) != replicate:
                raise RuntimeError("Gate F worker returned the wrong replicate index")
            if int(payload["seed"]) != _replicate_seed(replicate):
                raise RuntimeError("Gate F worker returned the wrong frozen seed")

            record = dict(payload["record"])
            if int(record["replicate"]) != replicate:
                raise RuntimeError("Gate F worker record index does not match its shard")
            records.append(V031SemiSyntheticReplicate(**record))

            current_train = int(payload["train_space_count"])
            current_heldout = int(payload["heldout_space_count"])
            current_block = str(payload["heldout_block"])
            if train_space_count is None:
                train_space_count = current_train
                heldout_space_count = current_heldout
                heldout_block = current_block
            elif (
                train_space_count != current_train
                or heldout_space_count != current_heldout
                or heldout_block != current_block
            ):
                raise RuntimeError("Gate F worker geometry metadata changed across replicates")

    if train_space_count is None or heldout_space_count is None or heldout_block is None:
        raise RuntimeError("Gate F produced no worker results")
    record_tuple = tuple(records)
    return V031SemiSyntheticResult(
        replicates=record_tuple,
        summary=summarize_v031_semisynthetic(record_tuple),
        train_space_count=train_space_count,
        heldout_space_count=heldout_space_count,
        heldout_block=heldout_block,
    )


def _run_coordinator(args: argparse.Namespace) -> int:
    from esdm.validate.v031_semisynthetic import V031_SEMISYNTHETIC_MANIFEST
    from esdm.validate.v031_semisynthetic_gate import evaluate_v031_semisynthetic_gate

    source_bytes, source_audit = _fetch_source()
    result = _run_isolated_benchmark(
        source_bytes,
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
        "execution": {
            "strategy": "sequential_fresh_python_process_per_replicate",
            "reason": "bound JAX/XLA memory lifetime without changing the frozen scientific profile",
        },
        "frozen_profile": {
            "replicates": FROZEN_REPLICATES,
            "base_seed": FROZEN_BASE_SEED,
            "seed_stride": FROZEN_SEED_STRIDE,
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
        "replicates": [
            asdict(row) | {"heldout_gain": row.heldout_gain}
            for row in result.replicates
        ],
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


def main() -> int:
    args = _parser().parse_args()
    if args._worker_replicate is not None:
        return _run_worker(args)
    if args._worker_source is not None or args._worker_output is not None:
        raise ValueError("internal Gate F worker paths require --_worker-replicate")
    return _run_coordinator(args)


if __name__ == "__main__":
    raise SystemExit(main())
