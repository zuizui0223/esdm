#!/usr/bin/env python3
"""Response-blind deployment-only precheck for the Queensland Wet Tropics E5 candidate."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
from urllib import request


PROJECT_ID = "ZAmir_QLD_Wet_Tropics_2022_WildObsID_0001"
API_URL = "https://camdbapi.wildobs.org.au/find"
ALLOWED_COLLECTIONS = {"metadata", "deployments"}
FORBIDDEN_RESPONSE_KEYS = {
    "observationID", "mediaID", "eventID", "eventStart", "eventEnd",
    "observationLevel", "observationType", "cameraSetupType",
    "scientificName", "count", "lifeStage", "sex", "behavior",
    "classificationMethod", "classificationProbability",
}
SAFE_DEPLOYMENT_KEYS = {
    "deploymentID", "locationID", "locationName", "latitude", "longitude",
    "coordinateUncertainty", "deploymentStart", "deploymentEnd", "setupBy",
    "cameraID", "cameraModel", "cameraDelay", "cameraHeight", "cameraDepth",
    "cameraTilt", "cameraHeading", "detectionDistance", "timestampIssues",
    "baitUse", "featureType", "habitat", "deploymentGroups", "deploymentTags",
    "deploymentComments", "projectName",
}


def _parse_time(value: object) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("empty deployment timestamp")
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _months_between(start: datetime, end: datetime) -> set[str]:
    if end < start:
        raise ValueError("deployment end precedes start")
    year, month = start.year, start.month
    out: set[str] = set()
    while (year, month) <= (end.year, end.month):
        out.add(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return out


def _location_key(row: dict) -> str:
    for field in ("locationID", "locationName"):
        value = str(row.get(field, "") or "").strip()
        if value:
            return f"{field}:{value}"
    return ""


def summarize_deployments(rows: list[dict]) -> dict:
    if not isinstance(rows, list) or not rows:
        raise ValueError("deployment response must be a non-empty list")

    leaked = sorted({
        key
        for row in rows
        for key in row
        if key in FORBIDDEN_RESPONSE_KEYS
    })
    if leaked:
        raise ValueError(f"response-bearing keys present in deployment query: {leaked!r}")

    safe_rows = [
        {key: row.get(key) for key in SAFE_DEPLOYMENT_KEYS if key in row}
        for row in rows
    ]

    ids = [str(row.get("deploymentID", "") or "").strip() for row in safe_rows]
    if any(not value for value in ids):
        raise ValueError("empty deploymentID")
    duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)

    locations = [_location_key(row) for row in safe_rows]
    missing_locations = sum(not value for value in locations)
    unique_locations = {value for value in locations if value}

    months: set[str] = set()
    parse_failures = 0
    nonpositive_intervals = 0
    starts: list[datetime] = []
    ends: list[datetime] = []
    for row in safe_rows:
        try:
            start = _parse_time(row.get("deploymentStart"))
            end = _parse_time(row.get("deploymentEnd"))
        except ValueError:
            parse_failures += 1
            continue
        starts.append(start)
        ends.append(end)
        if end <= start:
            nonpositive_intervals += 1
            continue
        months.update(_months_between(start, end))

    def _counts(field: str) -> dict[str, int]:
        values = [
            str(row.get(field, "") or "").strip()
            for row in safe_rows
        ]
        return dict(sorted(Counter(v for v in values if v).items()))

    coords = []
    for row in safe_rows:
        try:
            lat = float(row.get("latitude"))
            lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            continue
        coords.append((lat, lon))

    bbox = None
    if coords:
        bbox = {
            "min_latitude": min(lat for lat, _ in coords),
            "max_latitude": max(lat for lat, _ in coords),
            "min_longitude": min(lon for _, lon in coords),
            "max_longitude": max(lon for _, lon in coords),
        }

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "status": "E5_RESPONSE_BLIND_DEPLOYMENT_METADATA_PRECHECK",
        "response_boundary": {
            "collections_queried": ["deployments"],
            "observation_collection_queried": False,
            "media_collection_queried": False,
            "observation_rows_read": 0,
            "media_rows_read": 0,
            "species_fields_read": 0,
            "focal_response_opened": False,
        },
        "deployment_geometry": {
            "row_count": len(safe_rows),
            "unique_deployment_ids": len(set(ids)),
            "duplicate_deployment_ids": duplicates,
            "unique_physical_location_candidates": len(unique_locations),
            "rows_missing_location_identity": missing_locations,
            "parseable_interval_rows": len(starts),
            "timestamp_parse_failures": parse_failures,
            "nonpositive_interval_rows": nonpositive_intervals,
            "distinct_calendar_months_with_exposure": sorted(months),
            "distinct_calendar_month_count": len(months),
            "minimum_deployment_start": (
                min(starts).isoformat() if starts else None
            ),
            "maximum_deployment_end": (
                max(ends).isoformat() if ends else None
            ),
            "coordinate_bbox": bbox,
        },
        "protocol_metadata": {
            "camera_model_counts": _counts("cameraModel"),
            "feature_type_counts": _counts("featureType"),
            "habitat_counts": _counts("habitat"),
            "setup_by_counts": _counts("setupBy"),
            "camera_id_nonempty_rows": sum(
                bool(str(row.get("cameraID", "") or "").strip())
                for row in safe_rows
            ),
            "detection_distance_nonempty_rows": sum(
                bool(str(row.get("detectionDistance", "") or "").strip())
                for row in safe_rows
            ),
        },
        "preliminary_gate_hints": {
            "G2_SCHEMA_EFFORT_TIME": (
                "PASS_DEPLOYMENT_COMPONENT"
                if not duplicates and parse_failures == 0 and nonpositive_intervals == 0
                else "FAIL_OR_INCOMPLETE_DEPLOYMENT_COMPONENT"
            ),
            "G3_CROSSED_DOMAIN": "MANUAL_RESPONSE_BLIND_CROSS_TAB_REQUIRED",
            "G4_DETECTION_IDENTIFIABILITY": (
                "REPEATED_VISIT_PATH_REQUIRES_MODEL_FREEZE_AND_RESPONSE_SCHEMA_LATER"
            ),
            "G5_PHYSICAL_REPLICATION": (
                "POTENTIAL"
                if len(unique_locations) >= 30
                else "INSUFFICIENT_OR_UNRESOLVED"
            ),
            "G6_TEMPORAL_SUPPORT": (
                "POTENTIAL_GLOBAL_ONLY"
                if len(months) >= 6
                else "NO_GLOBAL_6_MONTH_SUPPORT"
            ),
            "G7_MODEL_FREEZE": "NOT_REACHED",
        },
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "split_specific_geometry_still_required": True,
        },
    }


def fetch_collection(api_key: str, collection: str, project_id: str) -> list[dict]:
    if collection not in ALLOWED_COLLECTIONS:
        raise ValueError(f"collection is not response-blind-authorized: {collection}")
    payload = json.dumps({
        "collection": collection,
        "filter": {"projectName": project_id},
    }).encode("utf-8")
    req = request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=90) as response:
        body = json.loads(response.read().decode("utf-8"))
    try:
        return body[0][1]
    except (TypeError, IndexError, KeyError) as exc:
        raise ValueError("unexpected WildObs API response shape") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--api-key-env", default="WILDOBSR_API_KEY")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise SystemExit(f"missing secret environment variable {args.api_key_env}")

    rows = fetch_collection(api_key, "deployments", PROJECT_ID)
    result = summarize_deployments(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
