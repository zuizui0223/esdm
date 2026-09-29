#!/usr/bin/env python3
"""Validate and freeze the one authorized E4 exact-sparse result."""
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


def _validate_compaction(result, checks):
    observed = result.get("compaction")
    if not isinstance(observed, dict):
        raise ValueError("scored E4 result must contain compaction")
    frozen = checks["compaction"]
    expected = {
        ("training", "compact_context_count"): frozen["training_compact_contexts"],
        ("training", "retained_keys_sha256"): frozen[
            "training_retained_keys_sha256"
        ],
        ("heldout", "compact_context_count"): frozen["heldout_compact_contexts"],
        ("heldout", "retained_keys_sha256"): frozen[
            "heldout_retained_keys_sha256"
        ],
    }
    for (section, field), value in expected.items():
        if observed.get(section, {}).get(field) != value:
            raise ValueError(f"E4 compaction drift: {section}.{field}")


def _validate_scored_result(result, contract):
    checks = contract["scored_result_checks"]
    required = tuple(checks["absolute_score_fields"])
    aggregate_tolerance = float(checks["aggregate_absolute_tolerance"])
    gain_tolerance = float(checks["gain_identity_absolute_tolerance"])

    scores = result.get("scores")
    rows = result.get("heldout_deployment_scores")
    if not isinstance(scores, dict) or not isinstance(rows, list):
        raise ValueError("scored E4 result must contain scores and heldout rows")

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
        activity_gain,
        full - activity_ko,
        rel_tol=0.0,
        abs_tol=gain_tolerance,
    ):
        raise ValueError("E4 activity gain identity failed")
    if not math.isclose(
        state_gain,
        full - state_ko,
        rel_tol=0.0,
        abs_tol=gain_tolerance,
    ):
        raise ValueError("E4 state gain identity failed")

    expected_n = int(checks["heldout_row_count"])
    if len(rows) != expected_n:
        raise ValueError(f"E4 heldout row count drift: {len(rows)} != {expected_n}")

    seen = set()
    sums = {name: 0.0 for name in required}
    for index, row in enumerate(rows):
        deployment = str(row.get("deploymentID", "")).strip()
        if not deployment or deployment in seen:
            raise ValueError("E4 deployment IDs must be unique non-empty")
        seen.add(deployment)
        for name in required:
            sums[name] += _finite(row[name], name=f"row[{index}].{name}")

    aggregates = {
        "full_heldout_log_score": full,
        "activity_knockout_heldout_log_score": activity_ko,
        "state_knockout_heldout_log_score": state_ko,
    }
    max_error = 0.0
    for name in required:
        row_mean = sums[name] / expected_n
        error = abs(row_mean - aggregates[name])
        max_error = max(max_error, error)
        if error > aggregate_tolerance:
            raise ValueError(f"E4 aggregate mismatch for {name}")

    divergences = result.get("divergences")
    if not isinstance(divergences, dict):
        raise ValueError("E4 scored result must contain divergences")
    pieces = [
        int(divergences.get("full", -1)),
        int(divergences.get("activity_knockout", -1)),
        int(divergences.get("state_knockout", -1)),
    ]
    if any(value < 0 for value in pieces):
        raise ValueError("E4 divergence counts missing or negative")
    total = int(divergences.get("total", -1))
    if total != sum(pieces):
        raise ValueError("E4 divergence total mismatch")

    serialization = result.get("odsp_serialization", {})
    if int(serialization.get("row_count", -1)) != expected_n:
        raise ValueError("E4 ODSP row count drift")
    if serialization.get("absolute_scores_serialized") is not True:
        raise ValueError("E4 absolute-score serialization missing")
    if serialization.get("gain_only_serialization") is not False:
        raise ValueError("E4 gain-only serialization is forbidden")

    _validate_compaction(result, checks)
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
        "compaction": result["compaction"],
    }


def freeze_result(
    result_path: Path,
    *,
    workflow_conclusion: str,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
):
    contract = _read("E4_MICA_SPARSE_RESULT_IMPORT_CONTRACT.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    identity = contract["required_identity"]

    for key in ("result_id", "programme_id", "endpoint_id", "fit_contract_id"):
        if result.get(key) != identity[key]:
            raise ValueError(f"E4 result identity mismatch: {key}")
    status = result.get("status")
    if status not in contract["accepted_statuses"]:
        raise ValueError("E4 result status is not importable")

    qualification = result.get("qualification", {})
    if qualification.get("result_sha256") != identity[
        "qualification_result_sha256"
    ]:
        raise ValueError("E4 qualification result binding drift")
    if qualification.get("fixture_fingerprint_sha256") != identity[
        "fixture_fingerprint_sha256"
    ]:
        raise ValueError("E4 qualification fixture fingerprint drift")

    allowed_conclusions = contract["workflow_conclusion_rules"][status]
    if str(workflow_conclusion) not in allowed_conclusions:
        raise ValueError(
            f"E4 workflow conclusion {workflow_conclusion!r} incompatible with {status}"
        )

    boundary = contract["interpretation_boundary"]
    decision = result.get("decision", {})
    exact_false = {
        "confirmatory_replication_claim": boundary[
            "confirmatory_replication_claim"
        ],
        "e3_rescue": boundary["e3_rescue_claim"],
        "causal_claim_authorized": boundary["causal_claim"],
        "parameter_recovery_claim_authorized": boundary[
            "parameter_recovery_claim"
        ],
        "same_programme_rerun_allowed": boundary[
            "same_programme_rerun_allowed"
        ],
    }
    for key, expected in exact_false.items():
        if decision.get(key) is not expected:
            raise ValueError(f"E4 decision boundary drift: {key}")

    summary = None
    if status in {"E4_SPARSE_EMPIRICAL_RESULT", "E4_SPARSE_SAMPLING_STOP"}:
        summary = _validate_scored_result(result, contract)
        if result.get("fixture_fingerprint_sha256") != identity[
            "fixture_fingerprint_sha256"
        ]:
            raise ValueError("E4 fitted fixture fingerprint drift")
        if status == "E4_SPARSE_EMPIRICAL_RESULT":
            if decision.get("sampling_gate_passed") is not True:
                raise ValueError("E4 empirical result requires sampling PASS")
            if summary["divergences"]["total"] != 0:
                raise ValueError("E4 sampling PASS requires zero divergences")
        else:
            if decision.get("sampling_gate_passed") is not False:
                raise ValueError("E4 sampling stop may not claim sampling PASS")
    elif status == "E4_SPARSE_EXECUTION_STOP":
        if decision.get("sampling_gate_passed") is not False:
            raise ValueError("E4 execution stop may not claim sampling PASS")
        if not str(result.get("reason", "")).strip():
            raise ValueError("E4 execution stop requires a reason")
    else:
        if decision.get("sampling_gate_passed") is not None:
            raise ValueError("E4 external-stop prewrite must leave sampling unevaluated")

    execution = contract["authorized_execution"]
    receipt = {
        "schema_version": 1,
        "programme_id": contract["programme_id"],
        "result_id": "e4-mica-exact-sparse-frozen-result-v1",
        "status": status,
        "frozen_date": "2026-09-30",
        "execution": {
            "workflow_run_id": execution["workflow_run_id"],
            "run_attempt": execution["run_attempt"],
            "authorization_head_sha": execution["authorization_head_sha"],
            "workflow_conclusion": str(workflow_conclusion),
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
            "backend_switch_within_e4_allowed": False,
            "result_values_may_change": False,
        },
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--workflow-conclusion", required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = freeze_result(
        args.result,
        workflow_conclusion=args.workflow_conclusion,
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
