#!/usr/bin/env python3
"""Mechanically adjudicate the frozen wild-pig activity-anchor outcome.

This script is intentionally outcome-agnostic: it accepts only the already-frozen
summary result JSON and the pre-outcome adjudication contract, re-derives the
SUPPORTED/UNRESOLVED/CONTRADICTED label, verifies the claim boundary, and emits
receipt + terminal-screen records. It does not fit or refit any ecological model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_ROUTE = "e5-external-activity-anchor-v1"
EXPECTED_RESULT_ID = "e5-wildpig-activity-anchor-transfer-result-v1"
EXPECTED_POST_CONTRACT = "e5-wildpig-activity-anchor-postoutcome-adjudication-v1"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classification(lower: float, upper: float) -> str:
    if lower > 0:
        return "SUPPORTED"
    if upper < 0:
        return "CONTRADICTED"
    return "UNRESOLVED"


def adjudicate(
    result: dict[str, Any],
    contract: dict[str, Any],
    *,
    run_id: int,
    job_id: int,
    artifact_id: int,
    artifact_digest: str,
    result_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if contract.get("contract_id") != EXPECTED_POST_CONTRACT:
        raise ValueError("unexpected post-outcome contract")
    if result.get("route_id") != EXPECTED_ROUTE:
        raise ValueError("route mismatch")
    if result.get("result_id") != EXPECTED_RESULT_ID:
        raise ValueError("result id mismatch")

    primary = result["primary_summary"]
    transfers = result["point_transfers"]
    boundary = result["route_boundary"]
    claims = result["claim_boundary"]

    if primary.get("total_transfers") != 8 or len(transfers) != 8:
        raise ValueError("frozen transfer count mismatch")
    if result.get("bootstrap", {}).get("replicates") != 1000:
        raise ValueError("frozen bootstrap count mismatch")

    lower = float(primary["bootstrap_median_gain_ci_lower"])
    upper = float(primary["bootstrap_median_gain_ci_upper"])
    expected = _classification(lower, upper)
    if result.get("status") != expected:
        raise ValueError("result status does not match frozen CI rule")
    if primary.get("interpretation") != expected:
        raise ValueError("primary interpretation does not match frozen CI rule")

    if boundary.get("original_G4_passed") is not False:
        raise ValueError("original G4 boundary drift")
    if boundary.get("absolute_detection_probability_identified") is not False:
        raise ValueError("absolute detection boundary drift")
    if boundary.get("abundance_identified") is not False:
        raise ValueError("abundance boundary drift")
    if boundary.get("untouched_preregistration") is not False:
        raise ValueError("preregistration boundary drift")
    if claims.get("original_E5_G4_pass_claim") is not False:
        raise ValueError("claim boundary drift")
    if claims.get("absolute_detection_claim") is not False:
        raise ValueError("absolute detection claim drift")
    if claims.get("abundance_claim") is not False:
        raise ValueError("abundance claim drift")
    if claims.get("causal_sensor_mechanism_claim") is not False:
        raise ValueError("causal mechanism claim drift")

    allowed_statuses = set(contract["decision_mapping"])
    if expected not in allowed_statuses:
        raise ValueError("unexpected frozen status")

    admissible = contract["admissible_result_fields"]
    receipt = {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "wolfson_wildpig_gps_camera_2015_2018",
        "route_id": EXPECTED_ROUTE,
        "receipt_id": "e5-wildpig-activity-anchor-outcome-receipt-v1",
        "status": "FROZEN_EMPIRICAL_OUTCOME_RECEIPT",
        "execution": {
            "workflow_run_id": int(run_id),
            "workflow_job_id": int(job_id),
            "artifact_id": int(artifact_id),
            "artifact_digest": artifact_digest,
            "result_json_sha256": result_sha256,
        },
        "adjudication": {
            "frozen_result_status": expected,
            "bootstrap_median_gain_ci_lower": lower,
            "bootstrap_median_gain_ci_upper": upper,
            "point_median_gain": primary["point_median_gain"],
            "point_minimum_gain": primary["point_minimum_gain"],
            "point_positive_gain_count": primary["point_positive_gain_count"],
            "total_transfers": 8,
        },
        "admissible_result_fields_contract": admissible,
        "postoutcome_rules_preserved": contract["postoutcome_rules"],
        "claim_boundary": contract["claim_boundary"],
    }

    terminal = {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "wolfson_wildpig_gps_camera_2015_2018",
        "route_id": EXPECTED_ROUTE,
        "screen_id": "e5-wildpig-activity-anchor-terminal-result-v1",
        "status": expected,
        "standard_e5": {
            "G4_DETECTION_IDENTIFIABILITY": contract["registry_update_rule"][
                "standard_E5_G4_must_remain"
            ],
            "candidate_qualified": False,
            "original_G4_reclassified": False,
        },
        "activity_anchor_route": {
            "terminal_empirical_result": True,
            "result_label": expected,
            "primary_summary": receipt["adjudication"],
            "point_transfers": transfers,
            "observed_sample_structure": result["observed_sample_structure"],
        },
        "claim_boundary": contract["claim_boundary"],
        "postoutcome_rules": contract["postoutcome_rules"],
    }
    return receipt, terminal


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--receipt-out", type=Path, required=True)
    p.add_argument("--terminal-out", type=Path, required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--job-id", type=int, required=True)
    p.add_argument("--artifact-id", type=int, required=True)
    p.add_argument("--artifact-digest", required=True)
    args = p.parse_args()

    result_bytes = args.result.read_bytes()
    result_sha = hashlib.sha256(result_bytes).hexdigest()
    result = json.loads(result_bytes.decode("utf-8"))
    contract = _load(args.contract)

    receipt, terminal = adjudicate(
        result,
        contract,
        run_id=args.run_id,
        job_id=args.job_id,
        artifact_id=args.artifact_id,
        artifact_digest=args.artifact_digest,
        result_sha256=result_sha,
    )
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.terminal_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.terminal_out.write_text(
        json.dumps(terminal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
