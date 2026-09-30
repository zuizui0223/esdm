#!/usr/bin/env python3
"""Response-blind Wildlife Insights metadata screener for E5 candidate discovery.

Only project/camera/deployment metadata are read. Detection-bearing image/sequence
tables are never opened by this script.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import json
from pathlib import Path
import re
from typing import Iterable


METADATA_FILES = {
    "projects": "projects.csv",
    "cameras": "cameras.csv",
    "deployments": "deployments.csv",
}
FORBIDDEN_RESPONSE_BASENAMES = {
    "images.csv",
    "sequences.csv",
    "detections.csv",
    "observations.csv",
}
MIN_MONTHS = 6
MIN_TOTAL_LOCATIONS_FOR_POSSIBLE_SPLIT = 30


def _norm(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())
    return value.strip("_")


def _find_csv(root: Path, basename: str) -> Path | None:
    target = basename.lower()
    matches = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name.lower() == target
    )
    if len(matches) > 1:
        raise ValueError(f"multiple {basename} files found: {matches!r}")
    return matches[0] if matches else None


def _read_csv(path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header")
        aliases = {_norm(name): name for name in reader.fieldnames}
        rows = [dict(row) for row in reader]
    return rows, aliases


def _column(aliases: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        key = _norm(candidate)
        if key in aliases:
            return aliases[key]
    return None


def _parse_date(value: str) -> date:
    raw = str(value).strip()
    if not raw:
        raise ValueError("empty date")
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unparseable date: {value!r}")


def _months_between(start: date, end: date) -> set[str]:
    if end < start:
        raise ValueError("deployment end precedes start")
    year, month = start.year, start.month
    result = set()
    while (year, month) <= (end.year, end.month):
        result.add(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return result


def _nonempty_values(rows: list[dict[str, str]], column: str | None) -> list[str]:
    if column is None:
        return []
    return [
        str(row.get(column, "")).strip()
        for row in rows
        if str(row.get(column, "")).strip()
    ]


def screen(package_dir: Path) -> dict:
    package_dir = package_dir.resolve()
    if not package_dir.is_dir():
        raise ValueError("package_dir must be a directory")

    response_presence = sorted(
        str(path.relative_to(package_dir))
        for path in package_dir.rglob("*")
        if path.is_file() and path.name.lower() in FORBIDDEN_RESPONSE_BASENAMES
    )

    found = {
        name: _find_csv(package_dir, basename)
        for name, basename in METADATA_FILES.items()
    }
    if found["projects"] is None or found["deployments"] is None:
        raise ValueError("projects.csv and deployments.csv are required")

    projects, project_aliases = _read_csv(found["projects"])
    deployments, deployment_aliases = _read_csv(found["deployments"])
    cameras = []
    camera_aliases: dict[str, str] = {}
    if found["cameras"] is not None:
        cameras, camera_aliases = _read_csv(found["cameras"])

    project_id_col = _column(
        deployment_aliases,
        ("project_id", "projectid", "project", "project_name"),
    )
    deployment_id_col = _column(
        deployment_aliases,
        ("deployment_id", "deploymentid", "camera_deployment_id", "deployment"),
    )
    location_col = _column(
        deployment_aliases,
        ("location_id", "location_name", "location", "site_name", "placename", "site"),
    )
    start_col = _column(
        deployment_aliases,
        ("start_date", "deployment_start", "deploymentstart", "start_datetime", "start"),
    )
    end_col = _column(
        deployment_aliases,
        ("end_date", "deployment_end", "deploymentend", "end_datetime", "end"),
    )
    lat_col = _column(deployment_aliases, ("latitude", "lat"))
    lon_col = _column(deployment_aliases, ("longitude", "lon", "lng", "long"))
    subproject_col = _column(
        deployment_aliases,
        ("subproject_name", "subproject", "stratum", "strata"),
    )

    required_columns = {
        "project": project_id_col,
        "deployment": deployment_id_col,
        "physical_location": location_col,
        "start": start_col,
        "end": end_col,
    }
    missing_required = sorted(
        name for name, column in required_columns.items() if column is None
    )
    geography_columns_present = lat_col is not None and lon_col is not None

    deployment_records = []
    invalid_dates = []
    duplicate_deployment_ids = set()
    seen_ids = set()
    for index, row in enumerate(deployments):
        deployment_id = (
            str(row.get(deployment_id_col, "")).strip()
            if deployment_id_col is not None else ""
        )
        if deployment_id:
            if deployment_id in seen_ids:
                duplicate_deployment_ids.add(deployment_id)
            seen_ids.add(deployment_id)

        start = end = None
        if start_col is not None and end_col is not None:
            try:
                start = _parse_date(row.get(start_col, ""))
                end = _parse_date(row.get(end_col, ""))
                if end < start:
                    raise ValueError("end before start")
            except Exception as exc:
                invalid_dates.append({"row": index, "reason": str(exc)})

        project = (
            str(row.get(project_id_col, "")).strip()
            if project_id_col is not None else ""
        )
        location = (
            str(row.get(location_col, "")).strip()
            if location_col is not None else ""
        )
        deployment_records.append(
            {
                "project": project,
                "deployment_id": deployment_id,
                "location": location,
                "start": start,
                "end": end,
                "subproject": (
                    str(row.get(subproject_col, "")).strip()
                    if subproject_col is not None else ""
                ),
            }
        )

    project_keys = sorted(
        {row["project"] for row in deployment_records if row["project"]}
    )
    if not project_keys:
        project_keys = ["__single_unspecified_project__"]

    per_project = []
    for project in project_keys:
        rows = [
            row for row in deployment_records
            if (
                row["project"] == project
                or (
                    project == "__single_unspecified_project__"
                    and not row["project"]
                )
            )
        ]
        locations = {row["location"] for row in rows if row["location"]}
        months: set[str] = set()
        valid_intervals = 0
        for row in rows:
            if row["start"] is not None and row["end"] is not None:
                valid_intervals += 1
                months.update(_months_between(row["start"], row["end"]))
        per_project.append(
            {
                "project": project,
                "deployment_rows": len(rows),
                "unique_physical_locations": len(locations),
                "distinct_calendar_months_with_exposure": len(months),
                "calendar_months": sorted(months),
                "valid_effort_intervals": valid_intervals,
                "subproject_values": sorted(
                    {row["subproject"] for row in rows if row["subproject"]}
                ),
                "six_month_temporal_hint": len(months) >= MIN_MONTHS,
                "thirty_location_split_hint": (
                    len(locations) >= MIN_TOTAL_LOCATIONS_FOR_POSSIBLE_SPLIT
                ),
            }
        )

    project_cluster_col = _column(
        project_aliases,
        (
            "project_sensor_cluster",
            "sensor_cluster",
            "camera_cluster",
            "cameras_clustered",
            "project_sensor_layout",
            "sensor_layout",
        ),
    )
    project_method_col = _column(
        project_aliases,
        ("project_sensor_method", "sensor_method", "camera_method"),
    )
    project_strat_col = _column(
        project_aliases,
        (
            "project_stratification_type",
            "project_stratification",
            "stratification_type",
            "stratification",
        ),
    )
    project_country_col = _column(
        project_aliases,
        ("focal_country", "country", "additional_countries"),
    )

    result = {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "screen_id": "e5-wildlife-insights-metadata-discovery-v1",
        "status": "RESPONSE_BLIND_METADATA_SCREEN",
        "response_boundary": {
            "response_files_opened": False,
            "response_rows_read": 0,
            "response_files_present_but_unread": response_presence,
            "allowed_files_read": [
                str(found[name].relative_to(package_dir))
                for name in ("projects", "cameras", "deployments")
                if found[name] is not None
            ],
        },
        "input_geometry": {
            "project_rows": len(projects),
            "camera_rows": len(cameras),
            "deployment_rows": len(deployments),
            "project_count_from_deployments": len(project_keys),
        },
        "schema": {
            "resolved_columns": {
                "project": project_id_col,
                "deployment": deployment_id_col,
                "physical_location": location_col,
                "start": start_col,
                "end": end_col,
                "latitude": lat_col,
                "longitude": lon_col,
                "subproject": subproject_col,
                "project_sensor_cluster_or_layout": project_cluster_col,
                "project_sensor_method": project_method_col,
                "project_stratification": project_strat_col,
                "project_country": project_country_col,
            },
            "missing_required_metadata_columns": missing_required,
            "geography_coordinates_present": geography_columns_present,
            "duplicate_deployment_ids": sorted(duplicate_deployment_ids),
            "invalid_effort_interval_count": len(invalid_dates),
            "invalid_effort_interval_examples": invalid_dates[:20],
        },
        "project_design_metadata": {
            "sensor_cluster_or_layout_values": sorted(
                set(_nonempty_values(projects, project_cluster_col))
            ),
            "sensor_method_values": sorted(
                set(_nonempty_values(projects, project_method_col))
            ),
            "stratification_values": sorted(
                set(_nonempty_values(projects, project_strat_col))
            ),
            "country_values": sorted(
                set(_nonempty_values(projects, project_country_col))
            ),
        },
        "projects": per_project,
        "preliminary_gate_hints": {
            "G2_SCHEMA_EFFORT_TIME": (
                "PARTIAL_DEPLOYMENT_METADATA_PASS_EVENT_SCHEMA_UNVERIFIED"
                if (
                    not missing_required
                    and geography_columns_present
                    and not duplicate_deployment_ids
                    and not invalid_dates
                )
                else "FAIL_OR_INCOMPLETE_DEPLOYMENT_METADATA"
            ),
            "G3_CROSSED_DOMAIN": "MANUAL_CROSSED_DOMAIN_REVIEW_REQUIRED",
            "G4_DETECTION_IDENTIFIABILITY": (
                "MANUAL_CALIBRATION_REVIEW_REQUIRED"
                if project_cluster_col is not None
                else "NO_CLUSTER_FIELD_DETECTED_MANUAL_REVIEW_REQUIRED"
            ),
            "G5_PHYSICAL_REPLICATION": (
                "POTENTIAL"
                if any(
                    row["thirty_location_split_hint"] for row in per_project
                )
                else "NO_PROJECT_WITH_30_LOCATIONS"
            ),
            "G6_TEMPORAL_SUPPORT": (
                "POTENTIAL"
                if any(row["six_month_temporal_hint"] for row in per_project)
                else "NO_PROJECT_WITH_6_MONTHS"
            ),
            "G7_MODEL_FREEZE": "NOT_REACHED",
        },
        "fail_closed_notes": [
            "This discovery screen cannot PASS G2 because event-time schema and taxonomic identity live outside the permitted metadata-only inputs and remain unverified.",
            "This discovery screen cannot PASS G3 because geography-by-source crossing requires a declared candidate split and design review.",
            "Cluster/paired-camera metadata alone cannot PASS G4; an independently identifying detection-calibration path must be demonstrated.",
            "A project with >=30 locations or >=6 calendar months only receives a discovery hint; E5 requires the final frozen training/heldout split itself to satisfy the thresholds.",
            "No focal response, detection count, diel direction, state frequency, or predictive score is read or used.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = screen(args.package_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "project_count": result["input_geometry"]["project_count_from_deployments"],
                "deployment_rows": result["input_geometry"]["deployment_rows"],
                "response_rows_read": result["response_boundary"]["response_rows_read"],
                "G2": result["preliminary_gate_hints"]["G2_SCHEMA_EFFORT_TIME"],
                "G5": result["preliminary_gate_hints"]["G5_PHYSICAL_REPLICATION"],
                "G6": result["preliminary_gate_hints"]["G6_TEMPORAL_SUPPORT"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
