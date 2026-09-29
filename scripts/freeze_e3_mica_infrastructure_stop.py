#!/usr/bin/env python3
"""Freeze terminal E3 infrastructure stop when the authorized fit yields no artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "replication" / "E3_MICA_REDUCED_INFRASTRUCTURE_STOP_POLICY.json"
IMPORT = ROOT / "docs" / "replication" / "E3_MICA_REDUCED_RESULT_IMPORT_CONTRACT.json"


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def freeze_infrastructure_stop(
    *,
    workflow_run_id: int,
    run_attempt: int,
    head_sha: str,
    head_branch: str,
    run_status: str,
    run_conclusion: str | None,
    artifact_count: int,
) -> dict:
    policy = _read(POLICY)
    contract = _read(IMPORT)
    expected = policy["applies_to"]
    frozen = contract["authorized_execution"]

    if int(workflow_run_id) != int(expected["fit_workflow_run_id"]):
        raise ValueError("authorized E3 workflow_run_id mismatch")
    if int(run_attempt) != int(expected["run_attempt"]):
        raise ValueError("authorized E3 run_attempt mismatch")
    if str(head_sha) != str(expected["authorization_head_sha"]):
        raise ValueError("authorized E3 head_sha mismatch")
    if str(head_branch) != str(expected["authorization_branch"]):
        raise ValueError("authorized E3 branch mismatch")

    if int(frozen["workflow_run_id"]) != int(workflow_run_id):
        raise ValueError("import contract workflow_run_id drifted")
    if int(frozen["run_attempt"]) != int(run_attempt):
        raise ValueError("import contract run_attempt drifted")
    if str(frozen["authorization_head_sha"]) != str(head_sha):
        raise ValueError("import contract authorization head drifted")
    if str(frozen["authorization_branch"]) != str(head_branch):
        raise ValueError("import contract authorization branch drifted")

    if str(run_status) != "completed":
        raise ValueError("infrastructure stop may freeze only a completed run")
    if int(artifact_count) != 0:
        raise ValueError("infrastructure stop requires zero canonical result artifacts")

    terminal = policy["terminal_receipt"]
    return {
        "schema_version": 1,
        "programme_id": "E3_MICA_EXP",
        "result_id": "e3-mica-reduced-infrastructure-stop-v1",
        "status": terminal["status"],
        "frozen_date": "2026-09-29",
        "fit_contract_id": "e3-mica-reduced-exploratory-fit-v1",
        "execution": {
            "workflow_run_id": int(workflow_run_id),
            "run_attempt": int(run_attempt),
            "authorization_head_sha": str(head_sha),
            "authorization_branch": str(head_branch),
            "workflow_status": str(run_status),
            "workflow_conclusion": None if run_conclusion is None else str(run_conclusion),
            "canonical_result_artifact_count": int(artifact_count),
            "canonical_result_artifact_name": policy["trigger_condition"][
                "canonical_result_artifact_name"
            ],
        },
        "scientific_result_available": False,
        "scored_result_available": False,
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
        "terminal_rule": {
            "same_programme_rerun_allowed": False,
            "post_result_threshold_retuning_allowed": False,
            "post_result_stream_retuning_allowed": False,
            "population_transfer_value_authorized": False,
            "odsp_audit_authorized": False,
        },
        "interpretation": policy["interpretation"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--run-status", required=True)
    parser.add_argument("--run-conclusion")
    parser.add_argument("--artifact-count", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = freeze_infrastructure_stop(
        workflow_run_id=args.workflow_run_id,
        run_attempt=args.run_attempt,
        head_sha=args.head_sha,
        head_branch=args.head_branch,
        run_status=args.run_status,
        run_conclusion=args.run_conclusion,
        artifact_count=args.artifact_count,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": receipt["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
