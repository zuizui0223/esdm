#!/usr/bin/env python3
"""Validate and freeze the one authorized E3 reduced exploratory result."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "replication"


def _read(name: str):
    return json.loads((DOCS / name).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value, *, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _validate_scored_result(result, contract):
    checks = contract["scored_result_checks"]
    required = tuple(checks["absolute_score_fields"])
    tolerance = float(checks["aggregate_absolute_tolerance"])
    gain_tolerance = float(checks["gain_identity_absolute_tolerance"])

    scores = result.get("scores")
    rows = result.get("heldout_deployment_scores")
    if not isinstance(scores, dict) or not isinstance(rows, list):
        raise ValueError("scored result must contain scores and heldout_deployment_scores")

    full = _finite(scores["full_heldout_log_score"], name="full score")
    activity_ko = _finite(
        scores["activity_knockout_heldout_log_score"],
        name="activity-knockout score",
    )
    state_ko = _finite(
        scores["state_knockout_heldout_log_score"],
        name="state-knockout score",
    )
    activity_gain = _finite(scores["activity_gain"], name="activity gain")
    state_gain = _finite(scores["state_gain"], name="state gain")

    if not math.isclose(
        activity_gain, full - activity_ko, rel_tol=0.0, abs_tol=gain_tolerance
    ):
        raise ValueError("activity gain identity failed")
    if not math.isclose(
        state_gain, full - state_ko, rel_tol=0.0, abs_tol=gain_tolerance
    ):
        raise ValueError("state gain identity failed")

    expected_n = int(checks["heldout_row_count"])
    if len(rows) != expected_n:
        raise ValueError(f"heldout row count drift: {len(rows)} != {expected_n}")

    seen = set()
    sums = {name: 0.0 for name in required}
    for index, row in enumerate(rows):
        deployment = str(row.get("deploymentID", "")).strip()
        if not deployment or deployment in seen:
            raise ValueError("heldout deployment IDs must be unique non-empty")
        seen.add(deployment)
        for name in required:
            value = _finite(row[name], name=f"row[{index}].{name}")
            sums[name] += value

    aggregate_map = {
        "full_heldout_log_score": full,
        "activity_knockout_heldout_log_score": activity_ko,
        "state_knockout_heldout_log_score": state_ko,
    }
    max_error = 0.0
    for name in required:
        row_mean = sums[name] / expected_n
        error = abs(row_mean - aggregate_map[name])
        max_error = max(max_error, error)
        if error > tolerance:
            raise ValueError(
                f"aggregate mismatch for {name}: {row_mean} != {aggregate_map[name]}"
            )

    serialization = result.get("odsp_serialization", {})
    if int(serialization.get("row_count", -1)) != expected_n:
        raise ValueError("ODSP row count drift")
    if serialization.get("absolute_scores_serialized") is not True:
        raise ValueError("absolute-score serialization missing")
    if serialization.get("gain_only_serialization") is not False:
        raise ValueError("gain-only serialization is forbidden")

    divergences = result.get("divergences", {})
    pieces = [
        int(divergences.get("full", -1)),
        int(divergences.get("activity_knockout", -1)),
        int(divergences.get("state_knockout", -1)),
    ]
    if any(value < 0 for value in pieces):
        raise ValueError("divergence counts missing or negative")
    total = int(divergences.get("total", -1))
    if total != sum(pieces):
        raise ValueError("divergence total mismatch")

    return {
        "scores": {
            "full_heldout_log_score": full,
            "activity_knockout_heldout_log_score": activity_ko,
            "state_knockout_heldout_log_score": state_ko,
            "activity_gain": activity_gain,
            "state_gain": state_gain,
        },
        "divergences": {
            "full": pieces[0],
            "activity_knockout": pieces[1],
            "state_knockout": pieces[2],
            "total": total,
        },
        "heldout_row_count": expected_n,
        "max_abs_aggregate_identity_error": max_error,
    }


def freeze_result(
    result_path: Path,
    *,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
):
    contract = _read("E3_MICA_REDUCED_RESULT_IMPORT_CONTRACT.json")
    fit_contract = _read("E3_MICA_REDUCED_FIT_CONTRACT.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    identity = contract["required_identity"]

    for key in ("result_id", "programme_id", "endpoint_id", "fit_contract_id"):
        if result.get(key) != identity[key]:
            raise ValueError(f"E3 result identity mismatch: {key}")
    if result.get("status") not in contract["accepted_statuses"]:
        raise ValueError("E3 result status is not importable")
    if result.get("capture_fixture_fingerprint_sha256") != identity[
        "fixture_fingerprint_sha256"
    ]:
        raise ValueError("E3 fixture fingerprint mismatch")

    decision = result.get("decision", {})
    boundary = contract["interpretation_boundary"]
    exact_false = {
        "confirmatory_replication_claim": boundary["confirmatory_replication_claim"],
        "e2_rescue": boundary["e2_rescue"],
        "causal_claim_authorized": boundary["causal_claim"],
        "parameter_recovery_claim_authorized": boundary["parameter_recovery_claim"],
        "same_programme_rerun_allowed": boundary["same_programme_rerun_allowed"],
    }
    for key, expected in exact_false.items():
        if decision.get(key) is not expected:
            raise ValueError(f"E3 decision boundary drift: {key}")

    scored = "scores" in result or "heldout_deployment_scores" in result
    summary = None
    if scored:
        summary = _validate_scored_result(result, contract)

    status = result["status"]
    if status == "E3_EXPLORATORY_RESULT":
        if not scored:
            raise ValueError("E3_EXPLORATORY_RESULT must contain scored output")
        if decision.get("sampling_gate_passed") is not True:
            raise ValueError("E3 result status requires sampling gate PASS")
        if summary["divergences"]["total"] != 0:
            raise ValueError("sampling PASS requires zero divergences")
    else:
        if decision.get("sampling_gate_passed") is not False:
            raise ValueError("sampling-stop result may not claim sampling PASS")
        if not scored and not str(result.get("reason", "")).strip():
            raise ValueError("unscored sampling stop requires a reason")

    execution = contract["authorized_execution"]
    receipt = {
        "schema_version": 1,
        "programme_id": "E3_MICA_EXP",
        "result_id": "e3-mica-reduced-frozen-result-v1",
        "status": status,
        "frozen_date": "2026-09-29",
        "fit_contract_id": fit_contract["contract_id"],
        "execution": {
            "workflow_run_id": execution["workflow_run_id"],
            "run_attempt": execution["run_attempt"],
            "authorization_head_sha": execution["authorization_head_sha"],
            "artifact_id": int(artifact_id),
            "artifact_name": str(artifact_name),
            "artifact_digest": str(artifact_digest),
            "result_json_sha256": _sha256(result_path),
        },
        "summary": summary,
        "decision": dict(decision),
        "result_reason": result.get("reason"),
        "interpretation_boundary": boundary,
        "terminal_rule": {
            "same_programme_rerun_allowed": False,
            "post_result_threshold_retuning_allowed": False,
            "post_result_stream_retuning_allowed": False,
            "result_values_may_change": False,
        },
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = freeze_result(
        args.result,
        artifact_id=args.artifact_id,
        artifact_name=args.artifact_name,
        artifact_digest=args.artifact_digest,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": receipt["status"],
        "result_json_sha256": receipt["execution"]["result_json_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
