#!/usr/bin/env python3
"""Run the frozen E3 reduced exploratory three-fit endpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from esdm.validate.e2_mica_fit import (
    FROZEN_NUM_CHAINS,
    FROZEN_NUM_SAMPLES,
    FROZEN_NUM_WARMUP,
    FROZEN_RNG_SEED_ACTIVITY,
    FROZEN_RNG_SEED_FULL,
    FROZEN_RNG_SEED_STATE,
    FROZEN_TARGET_ACCEPT,
    fit_e2_mica_empirical,
)
from esdm.validate.e3_mica_exploratory_fit import build_e3_mica_reduced_fixture


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    fit_contract = _read("E3_MICA_REDUCED_FIT_CONTRACT.json")

    if fit_contract["status"] != "FROZEN_FIT_NOT_AUTHORIZED":
        raise SystemExit("E3 fit contract status drifted")
    if fit_contract["execution"]["fit_authorized_now"] is not False:
        raise SystemExit("E3 implementation branch must not self-authorize fit")
    if _sha256(args.archive) != fit_contract["source"]["source_archive_sha256"]:
        raise SystemExit("E3 source archive hash drift")
    if _sha256(args.capture) != fit_contract["source"]["e3_capture_result_sha256"]:
        raise SystemExit("E3 capture result hash drift")

    capture = json.loads(args.capture.read_text(encoding="utf-8"))
    if capture.get("status") != fit_contract["source"]["required_capture_status"]:
        raise SystemExit("E3 fit requires frozen qualified reduced fixture")
    observed_capture_fp = capture["fixture_diagnostics"]["fixture_fingerprint_sha256"]
    if observed_capture_fp != fit_contract["source"]["required_fixture_fingerprint_sha256"]:
        raise SystemExit("E3 capture fixture fingerprint drifted")

    frozen_fit = fit_contract["fit"]
    observed_settings = {
        "num_warmup": FROZEN_NUM_WARMUP,
        "num_samples": FROZEN_NUM_SAMPLES,
        "num_chains": FROZEN_NUM_CHAINS,
        "target_accept_probability": FROZEN_TARGET_ACCEPT,
        "rng_seed_full": FROZEN_RNG_SEED_FULL,
        "rng_seed_activity_knockout": FROZEN_RNG_SEED_ACTIVITY,
        "rng_seed_state_knockout": FROZEN_RNG_SEED_STATE,
    }
    for key, value in observed_settings.items():
        if frozen_fit[key] != value:
            raise SystemExit(f"E3 inherited fit setting drifted: {key}")

    climate = json.loads(args.climate.read_text(encoding="utf-8"))
    try:
        fixture, diagnostics = build_e3_mica_reduced_fixture(
            source_archive=args.archive,
            climate_payload=climate,
            e2_full_contract=e2,
            e3_contract=e3,
            preflight_receipt=preflight,
            reduced_contract=reduced,
        )
        observed_fp = diagnostics["fixture_fingerprint_sha256"]
        if observed_fp != observed_capture_fp:
            raise ValueError("E3 reduced fixture changed between capture and fit")
        if diagnostics["state_calibration_stream_present_in_fit"] is not False:
            raise ValueError("E3 reduced fit unexpectedly retained state calibration")
        if diagnostics["state_calibration_rows_reused"] is not False:
            raise ValueError("E3 reduced fit unexpectedly reused calibration rows")
        if diagnostics["training_roles_reassigned"] is not False:
            raise ValueError("E3 reduced fit unexpectedly reassigned training roles")

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

        rows = list(fitted.heldout_deployment_scores)
        if len(rows) != int(fit_contract["outputs"]["heldout_row_count"]):
            raise ValueError("E3 heldout deployment row count drifted")
        required = tuple(fit_contract["outputs"]["absolute_scores_required"])
        for row in rows:
            missing = [name for name in required if name not in row]
            if missing:
                raise ValueError(f"E3 heldout row missing absolute scores: {missing!r}")

        sampling_passed = fitted.sampling_passed
        result = {
            "schema_version": 1,
            "result_id": "e3-mica-reduced-exploratory-result-v1",
            "programme_id": "E3_MICA_EXP",
            "endpoint_id": reduced["endpoint_id"],
            "status": (
                "E3_EXPLORATORY_RESULT"
                if sampling_passed
                else "E3_EXPLORATORY_SAMPLING_STOP"
            ),
            "capture_fixture_fingerprint_sha256": observed_capture_fp,
            "fit_contract_id": fit_contract["contract_id"],
            "scores": scores,
            "divergences": {
                "full": fitted.full_divergences,
                "activity_knockout": fitted.activity_knockout_divergences,
                "state_knockout": fitted.state_knockout_divergences,
                "total": fitted.total_divergences,
            },
            "parameter_summaries": fitted.parameter_summaries,
            "heldout_deployment_scores": rows,
            "odsp_serialization": {
                "row_count": len(rows),
                "row_unit": "one east-heldout deployment",
                "absolute_scores_serialized": True,
                "gain_only_serialization": False,
                "same_scored_cells_across_models": True,
            },
            "decision": {
                "sampling_gate_passed": sampling_passed,
                "activity_predictive_support_descriptive": bool(
                    sampling_passed and fitted.activity_gain > 0.0
                ),
                "state_predictive_support_descriptive": bool(
                    sampling_passed and fitted.state_gain > 0.0
                ),
                "minimum_effect_size_threshold": None,
                "confirmatory_replication_claim": False,
                "e2_rescue": False,
                "causal_claim_authorized": False,
                "parameter_recovery_claim_authorized": False,
                "same_programme_rerun_allowed": False,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": 3,
                "heldout_scores": 3,
                "state_calibration_stream_present_in_fit": False,
            },
        }
        exit_code = 0 if sampling_passed else 1
    except Exception as exc:
        result = {
            "schema_version": 1,
            "result_id": "e3-mica-reduced-exploratory-result-v1",
            "programme_id": "E3_MICA_EXP",
            "endpoint_id": reduced["endpoint_id"],
            "status": "E3_EXPLORATORY_SAMPLING_STOP",
            "fit_contract_id": fit_contract["contract_id"],
            "reason": f"{type(exc).__name__}: {exc}",
            "decision": {
                "sampling_gate_passed": False,
                "activity_predictive_support_descriptive": False,
                "state_predictive_support_descriptive": False,
                "minimum_effect_size_threshold": None,
                "confirmatory_replication_claim": False,
                "e2_rescue": False,
                "causal_claim_authorized": False,
                "parameter_recovery_claim_authorized": False,
                "same_programme_rerun_allowed": False,
            },
            "response_boundary": {
                "biological_response_already_consumed_under_e2": True,
                "model_fits": None,
                "heldout_scores": None,
                "state_calibration_stream_present_in_fit": False,
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
