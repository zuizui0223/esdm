#!/usr/bin/env python3
"""Consume the frozen E2 MICA full response once and run estimability checks only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from esdm.validate.e2_mica_full_response import build_e2_mica_empirical_fixture


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    response_blind = _read("E2_MICA_RESPONSE_BLIND_GEOMETRY_HEADER_RESULT.json")
    temporal = _read("E2_MICA_TEMPORAL_INTEGRITY_RESULT.json")

    climate_bytes = args.climate.read_bytes()
    climate_file_sha256 = hashlib.sha256(climate_bytes).hexdigest()
    expected_climate_result_sha256 = contract["climate"]["result_sha256"]
    if climate_file_sha256 != expected_climate_result_sha256:
        result = {
            "schema_version": 1,
            "result_id": "e2-mica-full-response-capture-v1",
            "status": "STOP_PRE_RESPONSE_CLIMATE_ARTIFACT_DRIFT",
            "reason": (
                f"climate result sha256 drift: {climate_file_sha256} != "
                f"{expected_climate_result_sha256}"
            ),
            "response_boundary": {
                "full_response_opened": False,
                "scientific_name_values_read": False,
                "count_values_read": False,
                "model_fits": 0,
                "heldout_scores": 0,
            },
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": result["status"], "reason": result["reason"]}))
        return 2

    climate = json.loads(climate_bytes)
    base = {
        "schema_version": 1,
        "result_id": "e2-mica-full-response-capture-v1",
        "candidate_id": "MICA_MUSKRAT",
        "source_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "climate_result_sha256": climate_file_sha256,
    }
    try:
        fixture = build_e2_mica_empirical_fixture(
            archive_path=args.archive,
            climate_payload=climate,
            response_blind_receipt=response_blind,
            temporal_receipt=temporal,
            full_contract=contract,
        )
    except Exception as exc:
        result = {
            **base,
            "status": "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY",
            "reason": f"{type(exc).__name__}: {exc}",
            "response_boundary": {
                "full_response_opened": True,
                "scientific_name_values_read": True,
                "count_values_read": True,
                "model_fits": 0,
                "heldout_scores": 0,
            },
            "decision": {
                "fit_authorized_from_capture": False,
                "same_programme_rerun_allowed": False,
            },
        }
        exit_code = 1
    else:
        result = {
            **base,
            "status": "RESPONSE_CAPTURE_QUALIFIED",
            "fixture_diagnostics": dict(fixture.diagnostics),
            "response_boundary": {
                "full_response_opened": True,
                "scientific_name_values_read": True,
                "count_values_read": True,
                "model_fits": 0,
                "heldout_scores": 0,
            },
            "decision": {
                "fit_authorized_from_capture": True,
                "same_programme_rerun_allowed": False,
            },
        }
        exit_code = 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "fixture_fingerprint_sha256": result.get(
            "fixture_diagnostics", {}
        ).get("fixture_fingerprint_sha256"),
        "reason": result.get("reason"),
    }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
