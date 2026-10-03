#!/usr/bin/env python3
"""Adjudicate the one authorized Queensland deployment-only capture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


RUN_ID = 37120434627
AUTHORIZATION_SHA = "697d790bcae523f5df9a9f0f5163cb555c38e2c3"
CANDIDATE_ID = "qld_wet_tropics_camtrapdp_2022_2023"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adjudicate(path: Path, *, artifact_id: int, artifact_name: str, artifact_digest: str) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("programme_id") != "E5_INDEPENDENT_ACTIVITY_DETECTION":
        raise ValueError("programme mismatch")
    if value.get("candidate_id") != CANDIDATE_ID:
        raise ValueError("candidate mismatch")

    boundary = value.get("response_boundary", {})
    if boundary.get("observation_collection_queried") is not False:
        raise ValueError("observation collection was queried")
    if boundary.get("media_collection_queried") is not False:
        raise ValueError("media collection was queried")
    if int(boundary.get("observation_rows_read", -1)) != 0:
        raise ValueError("observation rows were read")
    if int(boundary.get("media_rows_read", -1)) != 0:
        raise ValueError("media rows were read")
    if int(boundary.get("species_fields_read", -1)) != 0:
        raise ValueError("species fields were read")
    if boundary.get("focal_response_opened") is not False:
        raise ValueError("focal response was opened")

    status = str(value.get("status", ""))
    if status == "E5_DEPLOYMENT_CAPTURE_TRANSPORT_STOP":
        decision = value.get("decision", {})
        if decision.get("same_authorization_retry_allowed") is not False:
            raise ValueError("transport stop must forbid same-authorization retry")
        adjudication = {
            "status": "E5_QLD_DEPLOYMENT_CAPTURE_TERMINAL_TRANSPORT_STOP",
            "candidate_qualified": False,
            "geometry_available": False,
            "next_same_authorization_retry_allowed": False,
            "reason": str(value.get("reason", "")),
        }
    elif status == "E5_RESPONSE_BLIND_DEPLOYMENT_METADATA_PRECHECK":
        geometry = value.get("deployment_geometry", {})
        protocol = value.get("protocol_metadata", {})
        row_count = int(geometry.get("row_count", -1))
        unique_ids = int(geometry.get("unique_deployment_ids", -1))
        unique_locations = int(geometry.get("unique_physical_location_candidates", -1))
        months = int(geometry.get("distinct_calendar_month_count", -1))
        duplicates = list(geometry.get("duplicate_deployment_ids", []))
        parse_failures = int(geometry.get("timestamp_parse_failures", -1))
        nonpositive = int(geometry.get("nonpositive_interval_rows", -1))
        if row_count <= 0 or unique_ids != row_count:
            raise ValueError("deployment identity geometry invalid")
        if duplicates:
            raise ValueError("duplicate deployment IDs")
        if parse_failures != 0 or nonpositive != 0:
            raise ValueError("deployment interval integrity failed")
        if unique_locations <= 0:
            raise ValueError("physical location identity unavailable")

        adjudication = {
            "status": "E5_QLD_DEPLOYMENT_METADATA_CAPTURED",
            "candidate_qualified": False,
            "geometry_available": True,
            "deployment_rows": row_count,
            "unique_physical_locations": unique_locations,
            "global_distinct_calendar_months": months,
            "G2_deployment_component_passed": True,
            "G5_capacity_at_least_30_locations": unique_locations >= 30,
            "G6_global_six_month_capacity": months >= 6,
            "camera_model_counts": protocol.get("camera_model_counts", {}),
            "feature_type_counts": protocol.get("feature_type_counts", {}),
            "setup_by_counts": protocol.get("setup_by_counts", {}),
            "detection_distance_nonempty_rows": int(
                protocol.get("detection_distance_nonempty_rows", 0)
            ),
            "next_required_step": (
                "freeze response-blind geographic split and protocol crossing; "
                "then freeze the repeated-visit detection/activity model before "
                "any observation opening"
            ),
        }
    else:
        raise ValueError(f"unexpected Queensland capture status: {status!r}")

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": CANDIDATE_ID,
        "adjudication_id": "e5-qld-deployment-capture-adjudication-v1",
        "source_execution": {
            "workflow_run_id": RUN_ID,
            "authorization_sha": AUTHORIZATION_SHA,
            "artifact_id": int(artifact_id),
            "artifact_name": str(artifact_name),
            "artifact_digest": str(artifact_digest),
            "capture_json_sha256": _sha256(path),
        },
        "response_boundary": {
            "observation_rows_read": 0,
            "media_rows_read": 0,
            "species_fields_read": 0,
            "focal_response_opened": False,
            "candidate_qualification_authorized": False,
            "observation_opening_authorized": False,
            "model_fitting_authorized": False,
        },
        "adjudication": adjudication,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = adjudicate(
        args.capture,
        artifact_id=args.artifact_id,
        artifact_name=args.artifact_name,
        artifact_digest=args.artifact_digest,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
