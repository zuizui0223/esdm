#!/usr/bin/env python3
"""Validate and freeze the E3 MICA post-result ODSP audit artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


_ALLOWED_CATEGORY = {
    "robust_generalizing",
    "robust_non_generalizing",
    "uncertain",
    "mixed",
    "unavailable",
}
_ALLOWED_GROUP_STATUS = {
    "robust_positive",
    "robust_nonpositive",
    "uncertain",
    "unavailable",
}


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("E3 ODSP audit result must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite(value: object, *, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _validate_parallel(name: str, row: dict) -> dict:
    if int(row.get("row_count", -1)) != 733:
        raise ValueError(f"{name} row_count must be 733")
    if int(row.get("block_count", -1)) != 733:
        raise ValueError(f"{name} block_count must be 733")
    category = str(row.get("certified_category"))
    if category not in _ALLOWED_CATEGORY:
        raise ValueError(f"{name} certified category is invalid")
    group_status = str(row.get("certified_group_status"))
    if group_status not in _ALLOWED_GROUP_STATUS:
        raise ValueError(f"{name} group status is invalid")
    lower = _finite(row.get("certified_lower_bound"), name=f"{name}.lower")
    upper = _finite(row.get("certified_upper_bound"), name=f"{name}.upper")
    if lower > upper:
        raise ValueError(f"{name} certified interval is reversed")
    gain = _finite(row.get("point_mean_gain"), name=f"{name}.gain")
    if row.get("population_result_scientific_use_authorized") is not False:
        raise ValueError(f"{name} population result must remain unauthorized")
    return {
        "endpoint_id": str(row["endpoint_id"]),
        "lower_level": str(row["lower_level"]),
        "upper_level": str(row["upper_level"]),
        "point_mean_gain": gain,
        "certified_category": category,
        "certified_group_status": group_status,
        "certified_lower_bound": lower,
        "certified_upper_bound": upper,
        "point_transfer_ceiling": str(row["point_transfer_ceiling"]),
        "certified_transfer_ceiling": str(row["certified_transfer_ceiling"]),
        "row_count": 733,
        "block_count": 733,
    }


def freeze_audit(
    audit_path: Path,
    *,
    workflow_run_id: int,
    head_sha: str,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
) -> dict:
    audit = _read(audit_path)
    if audit.get("audit_id") != "e3-mica-odsp-parallel-audit-result-v1":
        raise ValueError("unexpected E3 ODSP audit_id")

    boundary = audit.get("boundary")
    if not isinstance(boundary, dict):
        raise ValueError("E3 ODSP audit boundary is missing")
    required_false = (
        "combined_three_level_filtration_authorized",
        "odsp_lattice_authorized",
        "population_superpopulation_interpretation_authorized",
        "n3_transfer_value_handoff_authorized",
        "e2_rescue",
        "confirmatory_replication",
        "causal_activity",
        "causal_state",
    )
    for key in required_false:
        if boundary.get(key) is not False:
            raise ValueError(f"E3 ODSP boundary drift: {key}")
    if boundary.get("parallel_not_ordered") is not True:
        raise ValueError("E3 activity/state must remain parallel and unordered")

    if audit.get("audit_status") == "NOT_AUTHORIZED_SOURCE_RESULT":
        if audit.get("odsp_executed") is not False:
            raise ValueError("blocked E3 audit may not execute ODSP")
        status = "ODSP_AUDIT_NOT_AUTHORIZED"
        result = None
        source_status = str(audit.get("source_status"))
    else:
        source = audit.get("source")
        if not isinstance(source, dict):
            raise ValueError("completed E3 ODSP audit is missing source")
        if source.get("programme_id") != "E3_MICA_EXP":
            raise ValueError("E3 ODSP source programme drifted")
        if source.get("status") != "E3_EXPLORATORY_RESULT":
            raise ValueError("completed E3 ODSP audit requires exploratory result")
        result = {
            "activity": _validate_parallel("activity", audit["activity"]),
            "state": _validate_parallel("state", audit["state"]),
        }
        status = "ODSP_AUDIT_COMPLETE"
        source_status = str(source["status"])

    digest = str(artifact_digest)
    if not digest.startswith("sha256:"):
        raise ValueError("artifact_digest must be a sha256 digest")

    return {
        "schema_version": 1,
        "receipt_id": "e3-mica-odsp-parallel-audit-frozen-v1",
        "frozen_date": "2026-09-29",
        "status": status,
        "source_status": source_status,
        "execution": {
            "workflow_run_id": int(workflow_run_id),
            "head_sha": str(head_sha),
            "artifact_id": int(artifact_id),
            "artifact_name": str(artifact_name),
            "artifact_digest": digest,
            "audit_result_sha256": _sha256(audit_path),
        },
        "parallel_result": result,
        "boundary": {
            "activity_state_parallel_not_ordered": True,
            "combined_three_level_filtration_authorized": False,
            "odsp_lattice_authorized": False,
            "population_superpopulation_interpretation_authorized": False,
            "n3_transfer_value_handoff_authorized": False,
            "e2_rescue": False,
            "confirmatory_replication": False,
            "causal_activity": False,
            "causal_state": False,
        },
        "terminal_rule": {
            "same_audit_result_values_may_change": False,
            "same_source_may_be_reaudited_with_different_odsp_commit": False,
            "post_result_ordering_selection_allowed": False,
            "post_result_population_promotion_allowed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-result", type=Path, required=True)
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = freeze_audit(
        args.audit_result,
        workflow_run_id=args.workflow_run_id,
        head_sha=args.head_sha,
        artifact_id=args.artifact_id,
        artifact_name=args.artifact_name,
        artifact_digest=args.artifact_digest,
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
