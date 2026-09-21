#!/usr/bin/env python3
"""Run the frozen v0.4-R3a identification-only qualification gate."""

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


FROZEN_GATE_COMMIT = "7fac98708d4474dc175d48c0ec3854f63d0ba527"
FROZEN_GATE_BLOB_SHA = "72ea44d467b41f78a0e9ec71941d8bb2ab26a227"
GATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "validation"
    / "V04_R3A_QUALIFICATION_GATE.md"
)

ANNOTATED_SITE_COUNT = 36
ANNOTATED_TIME_COUNT = 12
ANNOTATED_CONTEXT_COUNT = 432
CALIBRATED_SITE_COUNT = 18
CALIBRATED_CONTEXT_COUNT = 432

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
            "Frozen v0.4-R3a identification-only qualification. "
            "The 36 x 12 annotated design and all thresholds are not configurable."
        )
    )
    parser.add_argument(
        "--output",
        default="v04_r3a_qualification.json",
        help="audit JSON output path",
    )
    return parser


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _verify_gate_blob() -> str:
    if not GATE_PATH.exists():
        raise RuntimeError(f"frozen R3a gate file is missing: {GATE_PATH}")
    observed = _git_blob_sha1(GATE_PATH.read_bytes())
    if observed != FROZEN_GATE_BLOB_SHA:
        raise RuntimeError(
            "R3a gate blob mismatch: "
            f"expected {FROZEN_GATE_BLOB_SHA}, observed {observed}"
        )
    return observed


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
        headers={"User-Agent": "esdm-v04-r3a-qualification"},
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


def _json_safe(value):
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


def _initial_payload() -> dict:
    return {
        "schema": "esdm.v04_r3a.qualification.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "gate_freeze_commit": FROZEN_GATE_COMMIT,
        "gate_blob_sha": FROZEN_GATE_BLOB_SHA,
        "status": "INFRASTRUCTURE_BLOCKED",
        "infrastructure_block": {
            "stage": "coordinator_start",
            "reason": "R3a qualification has not completed",
        },
        "frozen_design": {
            "annotated_site_count": ANNOTATED_SITE_COUNT,
            "annotated_time_count": ANNOTATED_TIME_COUNT,
            "annotated_context_count": ANNOTATED_CONTEXT_COUNT,
            "calibrated_site_count": CALIBRATED_SITE_COUNT,
            "calibrated_context_count": CALIBRATED_CONTEXT_COUNT,
        },
    }


def _write_audit(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    from esdm.validate.v04_r3a_design import build_v04_r3a_fixture
    from esdm.validate.v04_r3a_gate import (
        evaluate_v04_r3a_identification,
        evaluate_v04_r3a_qualification,
        qualification_summary,
    )

    args = _parser().parse_args()
    output = Path(args.output)
    base_payload = _initial_payload()
    _write_audit(output, base_payload)

    try:
        observed_gate_blob = _verify_gate_blob()
        source_bytes, source_audit = _fetch_source()
        source_text = source_bytes.decode("utf-8")
        identification = evaluate_v04_r3a_identification(source_text)
        summary = qualification_summary(source_text, identification)
        decision = evaluate_v04_r3a_qualification(summary)
        fixture = build_v04_r3a_fixture(source_text)
    except Exception as exc:
        payload = dict(base_payload)
        payload["infrastructure_block"] = {
            "stage": "source_or_qualification",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        _write_audit(output, payload)
        return 2

    payload = dict(base_payload)
    payload.update(
        {
            "status": "PASS" if decision.passed else "FAIL",
            "infrastructure_block": None,
            "source_audit": source_audit,
            "observed_gate_blob_sha": observed_gate_blob,
            "selected_annotated_spaces": list(fixture.annotated_spaces),
            "selected_annotated_times": [
                [int(doy), int(hour)]
                for doy, hour in fixture.annotated_times
            ],
            "calibrated_spaces": list(fixture.calibrated_spaces),
            "identification": _identification_payload(identification),
            "summary": _json_safe(summary),
            "gate": {
                "passed": decision.passed,
                "checks": [
                    _json_safe(check)
                    for check in decision.checks
                ],
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


if __name__ == "__main__":
    raise SystemExit(main())
