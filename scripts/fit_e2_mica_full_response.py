#!/usr/bin/env python3
"""Fit the frozen E2 MICA endpoint from the immutable capture artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from esdm.validate.e2_mica_fit import fit_e2_mica_empirical
from esdm.validate.e2_mica_full_response import build_e2_mica_empirical_fixture


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    response_blind = _read("E2_MICA_RESPONSE_BLIND_GEOMETRY_HEADER_RESULT.json")
    temporal = _read("E2_MICA_TEMPORAL_INTEGRITY_RESULT.json")
    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    if capture.get("status") != "RESPONSE_CAPTURE_QUALIFIED":
        raise SystemExit("E2 MICA fit requires RESPONSE_CAPTURE_QUALIFIED")

    climate_bytes = args.climate.read_bytes()
    climate_sha256 = hashlib.sha256(climate_bytes).hexdigest()
    if climate_sha256 != contract["climate"]["result_sha256"]:
        raise SystemExit("E2 MICA fit climate artifact hash drift")
    climate = json.loads(climate_bytes)

    try:
        fixture = build_e2_mica_empirical_fixture(
            archive_path=args.archive,
            climate_payload=climate,
            response_blind_receipt=response_blind,
            temporal_receipt=temporal,
            full_contract=contract,
        )
        expected_fingerprint = capture["fixture_diagnostics"][
            "fixture_fingerprint_sha256"
        ]
        observed_fingerprint = fixture.diagnostics[
            "fixture_fingerprint_sha256"
        ]
        if observed_fingerprint != expected_fingerprint:
            raise ValueError(
                "E2 MICA captured fixture fingerprint changed before fit"
            )

        fitted = fit_e2_mica_empirical(
            fixture,
            progress_bar=False,
        )
        scores = {
            "full_heldout_log_score": fitted.full_heldout_log_score,
            "activity_knockout_heldout_log_score": (
                fitted.activity_knockout_heldout_log_score
            ),
            "state_knockout_heldout_log_score": (
                fitted.state_knockout_heldout_log_score
            ),
            "activity_gain": fitted.activity_gain,
            "state_gain": fitted.state_gain,
        }
        if not all(math.isfinite(float(value)) for value in scores.values()):
            raise ValueError("E2 MICA fit produced non-finite heldout score/gain")

        sampling_passed = fitted.sampling_passed
        result = {
            "schema_version": 1,
            "result_id": "e2-mica-empirical-result-v1",
            "status": (
                "EMPIRICAL_RESULT"
                if sampling_passed
                else "EMPIRICAL_SAMPLING_STOP"
            ),
            "candidate_id": "MICA_MUSKRAT",
            "capture_fixture_fingerprint_sha256": expected_fingerprint,
            "scores": scores,
            "divergences": {
                "full": fitted.full_divergences,
                "activity_knockout": fitted.activity_knockout_divergences,
                "state_knockout": fitted.state_knockout_divergences,
                "total": fitted.total_divergences,
            },
            "parameter_summaries": fitted.parameter_summaries,
            "heldout_deployment_scores": list(
                fitted.heldout_deployment_scores
            ),
            "odsp_serialization": {
                "row_count": len(fitted.heldout_deployment_scores),
                "row_unit": "one east-heldout deployment",
                "absolute_scores_serialized": True,
                "gain_only_serialization": False,
            },
            "decision": {
                "sampling_gate_passed": sampling_passed,
                "activity_predictive_support": (
                    bool(sampling_passed and fitted.activity_gain > 0.0)
                ),
                "state_predictive_support": (
                    bool(sampling_passed and fitted.state_gain > 0.0)
                ),
                "same_programme_rerun_allowed": False,
                "causal_claim_authorized": False,
            },
            "response_boundary": {
                "full_response_consumed": True,
                "model_fits": 3,
                "heldout_scores": 3,
            },
        }
        exit_code = 0 if sampling_passed else 1
    except Exception as exc:
        result = {
            "schema_version": 1,
            "result_id": "e2-mica-empirical-result-v1",
            "status": "EMPIRICAL_SAMPLING_STOP",
            "candidate_id": "MICA_MUSKRAT",
            "reason": f"{type(exc).__name__}: {exc}",
            "decision": {
                "sampling_gate_passed": False,
                "activity_predictive_support": False,
                "state_predictive_support": False,
                "same_programme_rerun_allowed": False,
                "causal_claim_authorized": False,
            },
            "response_boundary": {
                "full_response_consumed": True,
                "model_fits": None,
                "heldout_scores": None,
            },
        }
        exit_code = 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "activity_gain": result.get("scores", {}).get("activity_gain"),
        "state_gain": result.get("scores", {}).get("state_gain"),
        "sampling_gate_passed": result["decision"]["sampling_gate_passed"],
        "reason": result.get("reason"),
    }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
