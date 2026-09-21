#!/usr/bin/env python3
"""Run the frozen v0.4-R2 hard state/activity separation benchmark."""

from __future__ import annotations

import argparse
from dataclasses import fields, is_dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Mapping


FROZEN_GATE_COMMIT = "9e6db6fbe8336c6eb8bbe354713d2863fc40033f"
FROZEN_REPLICATES = 16
FROZEN_BASE_SEED = 20260926
FROZEN_SEED_STRIDE = 47
FROZEN_WARMUP = 300
FROZEN_SAMPLES = 350
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
            "Frozen v0.4-R2 hard separation gate: "
            f"replicates={FROZEN_REPLICATES}, seed={FROZEN_BASE_SEED}, "
            f"stride={FROZEN_SEED_STRIDE}, warmup={FROZEN_WARMUP}, "
            f"samples={FROZEN_SAMPLES}, chains={FROZEN_CHAINS}, "
            f"target_accept={FROZEN_TARGET_ACCEPT}. "
            "Scientific controls are intentionally not configurable."
        )
    )
    parser.add_argument(
        "--output",
        default="v04_r2_state_activity_gate.json",
        help="audit JSON output path",
    )
    parser.add_argument(
        "--progress-bar",
        action="store_true",
        help="show NumPyro progress bars; does not change frozen controls",
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
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _fetch_source() -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        FROZEN_SOURCE_URL,
        headers={"User-Agent": "esdm-v04-r2-hard-gate"},
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


def _read_worker_source(path: Path) -> bytes:
    payload = Path(path).read_bytes()
    observed_blob = _git_blob_sha1(payload)
    if observed_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "worker source blob mismatch: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, observed {observed_blob}"
        )
    return payload


def _json_safe(value):
    """Recursively convert frozen runtime objects to ordinary JSON-safe containers."""

    if is_dataclass(value):
        return {
            field.name: _json_safe(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if (
        value is None
        or isinstance(value, (str, int, float, bool))
    ):
        return value
    if hasattr(value, "value"):
        return _json_safe(value.value)
    return value


def _identification_payload(identification) -> dict:
    return {
        "positive_structural_pass": bool(
            identification.positive_structural_pass
        ),
        "positive_practical_pass": bool(
            identification.positive_practical_pass
        ),
        "sparse_structural_pass": bool(
            identification.sparse_structural_pass
        ),
        "sparse_practical_refused": bool(
            identification.sparse_practical_refused
        ),
        "unknown_detection_refused": bool(
            identification.unknown_detection_refused
        ),
        "positive_anchor_evidence": _json_safe(
            identification.positive_anchor_evidence
        ),
        "sparse_anchor_evidence": _json_safe(
            identification.sparse_anchor_evidence
        ),
        "unknown_anchor_evidence": _json_safe(
            identification.unknown_anchor_evidence
        ),
    }


def _pre_mcmc_failures(
    identification,
    *,
    extrapolation_integrity: bool,
) -> tuple[str, ...]:
    checks = (
        (
            "positive_structural_pass",
            bool(identification.positive_structural_pass),
        ),
        (
            "positive_practical_pass",
            bool(identification.positive_practical_pass),
        ),
        (
            "sparse_structural_pass",
            bool(identification.sparse_structural_pass),
        ),
        (
            "sparse_practical_refused",
            bool(identification.sparse_practical_refused),
        ),
        (
            "unknown_detection_refused",
            bool(identification.unknown_detection_refused),
        ),
        ("extrapolation_integrity", bool(extrapolation_integrity)),
    )
    return tuple(name for name, passed in checks if not passed)


def _write_audit(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _run_worker(args: argparse.Namespace) -> int:
    if args._worker_source is None or args._worker_output is None:
        raise ValueError("R2 worker requires internal source and output paths")

    from esdm.validate.v04_r2_run import run_v04_r2_replicate

    index = int(args._worker_replicate)
    seed = _replicate_seed(index)
    source_bytes = _read_worker_source(Path(args._worker_source))
    row = run_v04_r2_replicate(
        source_bytes.decode("utf-8"),
        replicate=index,
        seed=seed,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        credible_mass=FROZEN_CREDIBLE_MASS,
        progress_bar=bool(args.progress_bar),
        target_accept_prob=FROZEN_TARGET_ACCEPT,
    )
    payload = {
        "schema": "esdm.v04_r2.state_activity_gate.worker.v1",
        "replicate_index": index,
        "seed": seed,
        "record": _json_safe(row),
    }
    output = Path(args._worker_output)
    _write_audit(output, payload)
    print(
        json.dumps(
            {
                "replicate": index,
                "seed": seed,
                "worker_output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


def _initial_payload() -> dict:
    return {
        "schema": "esdm.v04_r2.state_activity_gate.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "status": "INFRASTRUCTURE_BLOCKED",
        "infrastructure_block": {
            "stage": "coordinator_start",
            "reason": "frozen R2 benchmark has not completed",
        },
        "execution": {
            "strategy": "sequential_fresh_python_process_per_replicate",
            "reason": (
                "bound JAX/XLA memory lifetime without changing frozen scientific controls"
            ),
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
    }


def _run_coordinator(args: argparse.Namespace) -> int:
    from esdm.validate.v031_semisynthetic import V031_SEMISYNTHETIC_MANIFEST
    from esdm.validate.v04_r2_gate import (
        evaluate_v04_r2_gate,
        evaluate_v04_r2_identification_profiles,
    )
    from esdm.validate.v04_r2_run import (
        V04R2Replicate,
        summarize_v04_r2,
    )
    from esdm.validate.v04_r2_state_activity import build_v04_r2_fixture

    output = Path(args.output)
    base_payload = _initial_payload()
    _write_audit(output, base_payload)

    try:
        source_bytes, source_audit = _fetch_source()
        source_text = source_bytes.decode("utf-8")
        identification = evaluate_v04_r2_identification_profiles(source_text)
        fixture = build_v04_r2_fixture(source_text, profile="positive")
    except Exception as exc:
        payload = dict(base_payload)
        payload["infrastructure_block"] = {
            "stage": "source_or_precheck",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        _write_audit(output, payload)
        return 2

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

    base_payload.update(
        {
            "source_audit": source_audit,
            "manifest": _json_safe(V031_SEMISYNTHETIC_MANIFEST),
            "train_space_count": len(fixture.train_spaces),
            "heldout_space_count": len(fixture.heldout_spaces),
            "calibration_space_count_positive": len(fixture.calibration_spaces),
            "extrapolation": {
                "training_max_eastness_z": train_max,
                "heldout_min_eastness_z": heldout_min,
                "integrity": extrapolation_integrity,
            },
            "identification": _identification_payload(identification),
        }
    )
    _write_audit(output, base_payload)

    pre_mcmc_failures = _pre_mcmc_failures(
        identification,
        extrapolation_integrity=extrapolation_integrity,
    )
    if pre_mcmc_failures:
        payload = dict(base_payload)
        payload.update(
            {
                "status": "FAIL",
                "infrastructure_block": None,
                "decision_stage": "pre_mcmc_required_conditions",
                "pre_mcmc_failures": list(pre_mcmc_failures),
                "replicates_executed": 0,
                "fits_executed": 0,
                "reason": (
                    "Frozen conjunction already contains a failed necessary "
                    "pre-MCMC condition; downstream recovery fits cannot "
                    "change the gate decision."
                ),
            }
        )
        _write_audit(output, payload)
        print(
            json.dumps(
                {
                    "output": str(output),
                    "status": "FAIL",
                    "decision_stage": payload["decision_stage"],
                    "pre_mcmc_failures": payload["pre_mcmc_failures"],
                },
                sort_keys=True,
            )
        )
        return 1

    records: list[V04R2Replicate] = []
    with tempfile.TemporaryDirectory(prefix="esdm-v04-r2-") as tmp:
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
                payload["status"] = "INFRASTRUCTURE_BLOCKED"
                payload["infrastructure_block"] = {
                    "stage": "worker_launch",
                    "replicate": replicate,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
                payload["completed_replicates"] = [
                    _json_safe(row) for row in records
                ]
                _write_audit(output, payload)
                return 2

            if completed.returncode != 0 or not worker_output.exists():
                payload = dict(base_payload)
                payload["status"] = "INFRASTRUCTURE_BLOCKED"
                payload["infrastructure_block"] = {
                    "stage": "worker_execution",
                    "replicate": replicate,
                    "worker_returncode": completed.returncode,
                    "reason": "worker process did not complete normally",
                }
                payload["completed_replicates"] = [
                    _json_safe(row) for row in records
                ]
                _write_audit(output, payload)
                return 2

            shard = json.loads(worker_output.read_text(encoding="utf-8"))
            if int(shard["replicate_index"]) != replicate:
                raise RuntimeError("R2 worker returned wrong replicate index")
            if int(shard["seed"]) != _replicate_seed(replicate):
                raise RuntimeError("R2 worker returned wrong frozen seed")
            record = dict(shard["record"])
            record["replicate"] = replicate
            records.append(V04R2Replicate(**record))

    summary = summarize_v04_r2(
        tuple(records),
        identification=identification,
        extrapolation_integrity=extrapolation_integrity,
    )
    decision = evaluate_v04_r2_gate(summary)
    payload = dict(base_payload)
    payload.update(
        {
            "status": "PASS" if decision.passed else "FAIL",
            "infrastructure_block": None,
            "replicates": [
                _json_safe(row)
                | {
                    "activity_gain": row.activity_gain,
                    "state_gain": row.state_gain,
                }
                for row in records
            ],
            "summary": _json_safe(summary),
            "gate": {
                "passed": decision.passed,
                "checks": [_json_safe(check) for check in decision.checks],
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
        raise ValueError("internal worker paths require --_worker-replicate")
    return _run_coordinator(args)


if __name__ == "__main__":
    raise SystemExit(main())
