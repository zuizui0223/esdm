#!/usr/bin/env python3
"""Run the frozen v0.3.2 Gate F-prime separation benchmark.

Scientific controls are intentionally not exposed as public CLI options. Each stochastic
replicate runs in a fresh Python process so JAX/XLA allocations cannot accumulate across
replicates. Worker interruption is recorded as INFRASTRUCTURE_BLOCKED rather than being
misreported as a scientific failure.
"""

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
FROZEN_BASE_SEED = 20260922
FROZEN_SEED_STRIDE = 41
FROZEN_WARMUP = 250
FROZEN_SAMPLES = 300
FROZEN_CHAINS = 2
FROZEN_CREDIBLE_MASS = 0.90
FROZEN_TARGET_ACCEPT = 0.90
FROZEN_SOURCE_COMMIT = "3dcb0a80c838ff9503e3957d7e004a7f4b888b0a"
FROZEN_SOURCE_PATH = "rain/annual_precipitation.csv"
FROZEN_SOURCE_BLOB_SHA = "40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949"
FROZEN_SOURCE_URL = (
    "https://raw.githubusercontent.com/the-pudding/data/"
    f"{FROZEN_SOURCE_COMMIT}/{FROZEN_SOURCE_PATH}"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Frozen v0.3.2 Gate F-prime profile: "
            f"replicates={FROZEN_REPLICATES}, seed={FROZEN_BASE_SEED}, "
            f"warmup={FROZEN_WARMUP}, samples={FROZEN_SAMPLES}, "
            f"chains={FROZEN_CHAINS}, target_accept={FROZEN_TARGET_ACCEPT}. "
            "Scientific controls are intentionally not configurable."
        )
    )
    parser.add_argument(
        "--output",
        default="v032_semisynthetic_gate_f_prime.json",
        help="audit JSON output path",
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
    value = os.environ.get("GITHUB_SHA")
    if value:
        return value
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def _fetch_source() -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v032-gate-f-prime"},
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


_build_worker_command = _worker_command


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
        raise ValueError("Gate F-prime worker requires internal source and output paths")

    from esdm.validate.v032_semisynthetic_run import run_v032_semisynthetic_benchmark

    index = int(args._worker_replicate)
    seed = _replicate_seed(index)
    source_bytes = _read_worker_source(Path(args._worker_source))
    result = run_v032_semisynthetic_benchmark(
        source_bytes.decode("utf-8"),
        replicates=1,
        base_seed=seed,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        credible_mass=FROZEN_CREDIBLE_MASS,
        progress_bar=bool(args.progress_bar),
        target_accept_prob=FROZEN_TARGET_ACCEPT,
    )
    row = result.replicates[0]
    record = asdict(row)
    record["replicate"] = index
    payload = {
        "schema": "esdm.v032.gate_f_prime.worker.v1",
        "replicate_index": index,
        "seed": seed,
        "record": record,
        "train_space_count": result.train_space_count,
        "heldout_space_count": result.heldout_space_count,
    }
    output = Path(args._worker_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"replicate": index, "seed": seed, "worker_output": str(output)}, sort_keys=True))
    return 0


def _write_audit(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_coordinator(args: argparse.Namespace) -> int:
    from esdm.validate.v031_semisynthetic import V031_SEMISYNTHETIC_MANIFEST
    from esdm.validate.v032_semisynthetic import build_v032_semisynthetic_fixture
    from esdm.validate.v032_semisynthetic_gate import (
        evaluate_v032_identification_profiles,
        evaluate_v032_semisynthetic_gate,
    )
    from esdm.validate.v032_semisynthetic_run import (
        V032SemiSyntheticReplicate,
        summarize_v032_semisynthetic,
    )

    output = Path(args.output)
    source_bytes, source_audit = _fetch_source()
    source_text = source_bytes.decode("utf-8")
    identification = evaluate_v032_identification_profiles(source_text)
    fixture = build_v032_semisynthetic_fixture(source_text, profile="positive")
    first_doy = fixture.model.domain.doy[0]
    first_hour = fixture.model.domain.hour[0]
    train_max = max(
        fixture.covariates[(space, first_doy, first_hour)]["eastness_z_train"]
        for space in fixture.train_spaces
    )
    heldout_min = min(
        fixture.covariates[(space, first_doy, first_hour)]["eastness_z_train"]
        for space in fixture.heldout_spaces
    )
    extrapolation_integrity = heldout_min > train_max

    base_payload = {
        "schema": "esdm.v032.gate_f_prime.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "execution": {
            "strategy": "sequential_fresh_python_process_per_replicate",
            "reason": "bound JAX/XLA memory lifetime without changing frozen scientific controls",
        },
        "frozen_profile": {
            "replicates": FROZEN_REPLICATES,
            "base_seed": FROZEN_BASE_SEED,
            "seed_stride": FROZEN_SEED_STRIDE,
            "num_warmup": FROZEN_WARMUP,
            "num_samples": FROZEN_SAMPLES,
            "num_chains": FROZEN_CHAINS,
            "credible_mass": FROZEN_CREDIBLE_MASS,
            "target_accept_prob": FROZEN_TARGET_ACCEPT,
        },
        "source_audit": source_audit,
        "manifest": asdict(V031_SEMISYNTHETIC_MANIFEST),
        "train_space_count": len(fixture.train_spaces),
        "heldout_space_count": len(fixture.heldout_spaces),
        "calibration_space_count_positive": len(fixture.calibration_spaces),
        "extrapolation": {
            "training_max_eastness_z": train_max,
            "heldout_min_eastness_z": heldout_min,
            "integrity": extrapolation_integrity,
        },
        "identification": {
            "positive_structural_pass": identification.positive_structural_pass,
            "positive_practical_pass": identification.positive_practical_pass,
            "negative_structural_pass": identification.negative_structural_pass,
            "negative_practical_refused": identification.negative_practical_refused,
        },
    }

    records: list[V032SemiSyntheticReplicate] = []
    with tempfile.TemporaryDirectory(prefix="esdm-v032-gate-f-prime-") as tmp:
        workdir = Path(tmp)
        source_path = workdir / "pinned_source.csv"
        source_path.write_bytes(source_bytes)
        for replicate in range(FROZEN_REPLICATES):
            worker_output = workdir / f"replicate-{replicate:02d}.json"
            command = _worker_command(
                replicate=replicate,
                source_path=source_path,
                output_path=worker_output,
                progress_bar=bool(args.progress_bar),
            )
            try:
                completed = subprocess.run(command, check=False)
            except Exception as exc:
                payload = dict(base_payload)
                payload.update(
                    {
                        "status": "INFRASTRUCTURE_BLOCKED",
                        "infrastructure_block": {
                            "replicate": replicate,
                            "reason": f"worker launch failed: {type(exc).__name__}: {exc}",
                        },
                        "completed_replicates": [asdict(row) for row in records],
                    }
                )
                _write_audit(output, payload)
                return 2
            if completed.returncode != 0 or not worker_output.exists():
                payload = dict(base_payload)
                payload.update(
                    {
                        "status": "INFRASTRUCTURE_BLOCKED",
                        "infrastructure_block": {
                            "replicate": replicate,
                            "worker_returncode": completed.returncode,
                            "reason": "worker process did not complete normally",
                        },
                        "completed_replicates": [asdict(row) for row in records],
                    }
                )
                _write_audit(output, payload)
                return 2

            shard = json.loads(worker_output.read_text(encoding="utf-8"))
            if int(shard["replicate_index"]) != replicate:
                raise RuntimeError("Gate F-prime worker returned wrong replicate index")
            if int(shard["seed"]) != _replicate_seed(replicate):
                raise RuntimeError("Gate F-prime worker returned wrong frozen seed")
            record = dict(shard["record"])
            record["replicate"] = replicate
            records.append(V032SemiSyntheticReplicate(**record))

    summary = summarize_v032_semisynthetic(
        tuple(records),
        identification=identification,
        extrapolation_integrity=extrapolation_integrity,
    )
    decision = evaluate_v032_semisynthetic_gate(summary)
    payload = dict(base_payload)
    payload.update(
        {
            "status": "PASS" if decision.passed else "FAIL",
            "replicates": [asdict(row) | {"heldout_gain": row.heldout_gain} for row in records],
            "summary": asdict(summary),
            "gate_f_prime": {
                "passed": decision.passed,
                "checks": [asdict(check) for check in decision.checks],
            },
        }
    )
    _write_audit(output, payload)
    print(
        json.dumps(
            {
                "output": str(output),
                "status": payload["status"],
                "git_sha": payload["git_sha"],
                "source_sha256": source_audit["sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if decision.passed else 1


def main() -> int:
    args = _parser().parse_args()
    if args._worker_replicate is not None:
        return _run_worker(args)
    if args._worker_source is not None or args._worker_output is not None:
        raise ValueError("internal Gate F-prime worker paths require --_worker-replicate")
    return _run_coordinator(args)


if __name__ == "__main__":
    raise SystemExit(main())
