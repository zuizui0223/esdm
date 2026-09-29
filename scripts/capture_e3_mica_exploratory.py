#!/usr/bin/env python3
"""Build the E3 exploratory MICA fixture and stop before model fitting."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from esdm.validate.e3_mica_exploratory_fit import (
    build_e3_mica_reduced_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    e2 = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    e3 = _read("E3_MICA_EXPLORATORY_CONTRACT.json")
    preflight = _read("E3_MICA_EXPLORATORY_PREFLIGHT_RESULT.json")
    reduced = _read("E3_MICA_REDUCED_ENDPOINT_CONTRACT.json")
    climate = json.loads(args.climate.read_text(encoding="utf-8"))

    if e3["status"] != "PREFLIGHT_PASS_FIT_NOT_AUTHORIZED":
        raise SystemExit("E3 capture requires frozen PREFLIGHT_PASS_FIT_NOT_AUTHORIZED")
    if e3["execution"]["exploratory_fit_authorized_now"] is not False:
        raise SystemExit("E3 capture branch must not authorize fitting")

    base = {
        "schema_version": 1,
        "result_id": "e3-mica-exploratory-capture-v1",
        "programme_id": "E3_MICA_EXP",
        "source_archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
    }
    if reduced["status"] not in {
        "FROZEN_POST_FULL_CAPTURE_STOP_FIT_NOT_AUTHORIZED",
        "REDUCED_FIXTURE_QUALIFIED_FIT_NOT_AUTHORIZED",
    }:
        raise SystemExit("E3 reduced endpoint contract is not frozen pre-fit")
    if reduced["execution"]["exploratory_model_fit_authorized_now"] is not False:
        raise SystemExit("E3 reduced capture must not authorize model fitting")

    try:
        fixture, diagnostics = build_e3_mica_reduced_fixture(
            source_archive=args.archive,
            climate_payload=climate,
            e2_full_contract=e2,
            e3_contract=e3,
            preflight_receipt=preflight,
            reduced_contract=reduced,
        )
    except Exception as exc:
        result = {
            **base,
            "status": "E3_CAPTURE_STOP",
            "reason": f"{type(exc).__name__}: {exc}",
            "decision": {
                "fixture_qualified": False,
                "exploratory_fit_authorized_by_this_result": False,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": 0,
                "heldout_scores": 0,
            },
        }
        code = 1
    else:
        result = {
            **base,
            "status": "E3_REDUCED_FIXTURE_QUALIFIED",
            "fixture_diagnostics": diagnostics,
            "fixture_summary": {
                "training_spaces": len(fixture.train_spaces),
                "heldout_spaces": len(fixture.heldout_spaces),
                "stream_counts": {
                    name: sum(value == name for value in fixture.stream_by_space.values())
                    for name in (
                        "opportunistic_presence",
                        "calibrated_presence",
                        "state_annotated",
                        "state_calibration",
                        "heldout_state_annotated",
                    )
                },
                "model_stream_names": [
                    stream.name for stream in fixture.model.streams
                ],
                "state_counts": diagnostics["state_counts"],
            },
            "decision": {
                "fixture_qualified": True,
                "full_endpoint_state_calibration_gate_passed": False,
                "state_calibration_stream_present_in_fit": False,
                "state_calibration_rows_reused": False,
                "exploratory_fit_authorized_by_this_result": False,
                "requires_separate_pure_authorization_marker": True,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": 0,
                "heldout_scores": 0,
            },
        }
        code = 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "training_spaces": result.get("fixture_summary", {}).get("training_spaces"),
        "heldout_spaces": result.get("fixture_summary", {}).get("heldout_spaces"),
        "reason": result.get("reason"),
    }, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
