#!/usr/bin/env python3
"""Run the frozen E3 reduced exploratory MICA fit once."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from esdm.validate.e2_mica_fit import fit_e2_mica_empirical
from esdm.validate.e3_mica_exploratory_fit import build_e3_mica_reduced_fixture


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    e2 = _read("E2_MICA_FULL_RESPONSE_CONTRACT.json")
    e3 = _read("E3_MICA_EXPLORATORY_CONTRACT.json")
    preflight = _read("E3_MICA_EXPLORATORY_PREFLIGHT_RESULT.json")
    reduced = _read("E3_MICA_REDUCED_ENDPOINT_CONTRACT.json")
    fit_contract = _read("E3_MICA_EXPLORATORY_FIT_CONTRACT.json")

    if fit_contract["status"] != "FROZEN_PRE_FIT_NOT_AUTHORIZED":
        raise SystemExit("E3 fit contract is not frozen pre-fit")
    if fit_contract["execution"]["exploratory_fit_authorized_now"] is not False:
        raise SystemExit("E3 implementation branch must not self-authorize fitting")
    if reduced["status"] != "REDUCED_FIXTURE_QUALIFIED_FIT_NOT_AUTHORIZED":
        raise SystemExit("E3 reduced fixture is not qualified for separate authorization")

    capture_bytes = args.capture.read_bytes()
    capture_sha256 = hashlib.sha256(capture_bytes).hexdigest()
    binding = fit_contract["fixture_binding"]
    if capture_sha256 != binding["capture_result_sha256"]:
        raise SystemExit(
            f"E3 capture result sha256 drift: {capture_sha256} != "
            f"{binding['capture_result_sha256']}"
        )
    capture = json.loads(capture_bytes)
    if capture.get("status") != "E3_REDUCED_FIXTURE_QUALIFIED":
        raise SystemExit("E3 fit requires E3_REDUCED_FIXTURE_QUALIFIED")
    observed_capture_fp = capture["fixture_diagnostics"]["fixture_fingerprint_sha256"]
    if observed_capture_fp != binding["fixture_fingerprint_sha256"]:
        raise SystemExit("E3 capture fixture fingerprint drift")

    climate = json.loads(args.climate.read_text(encoding="utf-8"))
    fixture, diagnostics = build_e3_mica_reduced_fixture(
        source_archive=args.archive,
        climate_payload=climate,
        e2_full_contract=e2,
        e3_contract=e3,
        preflight_receipt=preflight,
        reduced_contract=reduced,
    )
    observed_fp = diagnostics["fixture_fingerprint_sha256"]
    if observed_fp != binding["fixture_fingerprint_sha256"]:
        raise SystemExit("E3 rebuilt fixture fingerprint drift before fit")
    if len(fixture.train_spaces) != binding["training_spaces"]:
        raise SystemExit("E3 training-space count drift before fit")
    if len(fixture.heldout_spaces) != binding["heldout_spaces"]:
        raise SystemExit("E3 heldout-space count drift before fit")
    stream_names = [stream.name for stream in fixture.model.streams]
    if stream_names != binding["model_stream_names"]:
        raise SystemExit("E3 reduced model stream set drift before fit")

    try:
        fitted = fit_e2_mica_empirical(fixture, progress_bar=False)
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
            raise ValueError("E3 fit produced non-finite heldout score/gain")

        sampling_passed = fitted.sampling_passed
        result = {
            "schema_version": 1,
            "result_id": "e3-mica-exploratory-fit-v1",
            "programme_id": "E3_MICA_EXP",
            "endpoint_id": fit_contract["endpoint_id"],
            "status": (
                "E3_EXPLORATORY_RESULT"
                if sampling_passed
                else "E3_EXPLORATORY_SAMPLING_STOP"
            ),
            "classification": "exploratory_real_data_analysis",
            "fixture_binding": {
                "capture_result_sha256": capture_sha256,
                "fixture_fingerprint_sha256": observed_fp,
                "training_spaces": len(fixture.train_spaces),
                "heldout_spaces": len(fixture.heldout_spaces),
                "model_stream_names": stream_names,
            },
            "scores": scores,
            "divergences": {
                "full": fitted.full_divergences,
                "activity_knockout": fitted.activity_knockout_divergences,
                "state_knockout": fitted.state_knockout_divergences,
                "total": fitted.total_divergences,
            },
            "parameter_summaries": fitted.parameter_summaries,
            "heldout_deployment_scores": list(fitted.heldout_deployment_scores),
            "odsp_serialization": {
                "row_count": len(fitted.heldout_deployment_scores),
                "row_unit": "one east-heldout deployment",
                "absolute_scores_serialized": True,
                "gain_only_serialization": False,
            },
            "decision": {
                "sampling_gate_passed": sampling_passed,
                "activity_gain_positive": bool(
                    sampling_passed and fitted.activity_gain > 0.0
                ),
                "state_gain_positive": bool(
                    sampling_passed and fitted.state_gain > 0.0
                ),
                "independently_calibrated_state_effect_authorized": False,
                "confirmatory_replication_authorized": False,
                "causal_claim_authorized": False,
                "e2_rescue_authorized": False,
                "same_programme_rerun_allowed": False,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": 3,
                "heldout_scores": 3,
            },
        }
        code = 0
    except Exception as exc:
        result = {
            "schema_version": 1,
            "result_id": "e3-mica-exploratory-fit-v1",
            "programme_id": "E3_MICA_EXP",
            "endpoint_id": fit_contract["endpoint_id"],
            "status": "E3_EXPLORATORY_EXECUTION_STOP",
            "classification": "exploratory_real_data_analysis",
            "reason": f"{type(exc).__name__}: {exc}",
            "fixture_binding": {
                "capture_result_sha256": capture_sha256,
                "fixture_fingerprint_sha256": observed_fp,
            },
            "decision": {
                "sampling_gate_passed": False,
                "activity_gain_positive": False,
                "state_gain_positive": False,
                "independently_calibrated_state_effect_authorized": False,
                "confirmatory_replication_authorized": False,
                "causal_claim_authorized": False,
                "e2_rescue_authorized": False,
                "same_programme_rerun_allowed": False,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": None,
                "heldout_scores": None,
            },
        }
        code = 1

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
    return code


if __name__ == "__main__":
    raise SystemExit(main())
