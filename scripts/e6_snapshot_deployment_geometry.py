#!/usr/bin/env python3
"""Response-blind SNAPSHOT USA source/geometry qualification.

Only the two published deployment CSVs are read. No camera observation
sequences, species counts, diel counts or biological outcomes are opened.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from math import floor, isfinite
from pathlib import Path

SOURCES = {
    "history": {
        "filename": "ssusa_finaldeployments.csv",
        "sha256": "9e837bba556de86af5934abcb5d8a487206df2b340a8b28fa8cc135c7bb7ec56",
        "file_id": 4016828,
    },
    "holdout_2024": {
        "filename": "ssusa_2024_deployments.csv",
        "sha256": "b742e8789fa18c83713f2dec76e342857c122c012ee464db5563f3b06d29970d",
        "file_id": 4788613,
    },
}
LOW = {"wild", "rural"}
HIGH = {"suburban", "urban"}
REQUIRED = {
    "Camera_Trap_Array", "Deployment_ID", "Site_Name", "Development_Level",
    "Latitude", "Longitude", "Start_Date", "End_Date"
}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _year(v: str, start: str) -> int:
    if str(v).strip():
        return int(float(str(v).strip()))
    return date.fromisoformat(start.strip()[:10]).year


def audit_deployments(path: Path, cohort: str) -> dict:
    spec = SOURCES[cohort]
    if file_sha256(path) != spec["sha256"]:
        raise ValueError("official pinned Dryad deployment digest mismatch")
    rows = 0
    by_level, by_year, by_group = Counter(), Counter(), Counter()
    excluded = Counter()
    arrays = defaultdict(set)
    sites = set()
    deployment_ids = {}
    shared_grids = defaultdict(set)
    qualifying_site_years = defaultdict(set)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not REQUIRED.issubset(set(reader.fieldnames or ())):
            raise ValueError(f"missing required deployment headers: {sorted(REQUIRED-set(reader.fieldnames or ()))}")
        for row in reader:
            rows += 1
            key = str(row["Deployment_ID"]).strip()
            arr = str(row["Camera_Trap_Array"]).strip()
            site = str(row["Site_Name"]).strip()
            dev = str(row["Development_Level"]).strip().lower()
            by_level[dev or "MISSING"] += 1
            if not key or not arr or not site:
                excluded["missing_identity"] += 1
                continue
            if dev not in LOW | HIGH:
                excluded["missing_or_unknown_development"] += 1
                continue
            try:
                year = _year(row.get("Year", ""), row["Start_Date"])
                start = date.fromisoformat(row["Start_Date"].strip()[:10])
                end = date.fromisoformat(row["End_Date"].strip()[:10])
                lat, lon = float(row["Latitude"]), float(row["Longitude"])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180 and
                        isfinite(lat) and isfinite(lon) and end > start):
                    raise ValueError("nonfinite coordinates or invalid interval")
            except (ValueError, TypeError, OverflowError):
                excluded["invalid_deployment_dates_or_geography"] += 1
                continue
            if cohort == "history" and year not in (2019, 2020, 2021, 2022, 2023):
                excluded["outside_pinned_year_partition"] += 1
                continue
            if cohort == "holdout_2024" and year != 2024:
                excluded["outside_pinned_year_partition"] += 1
                continue
            # Physical-camera site and development should agree within each
            # deployment ID. Duplicated rows may occur; ambiguous IDs are
            # quarantined for later source-only application.
            signature = (arr, site, dev, year, lat, lon)
            if key in deployment_ids and deployment_ids[key] != signature:
                excluded["conflicting_duplicate_deployment_id_rows"] += 1
            elif key in deployment_ids:
                excluded["identical_duplicate_deployment_id_rows"] += 1
            else:
                deployment_ids[key] = signature
            group = "low" if dev in LOW else "high"
            by_year[year] += 1
            by_group[group] += 1
            arrays[(arr, group)].add(year)
            sites.add((arr, site, year))
            shared_grids[(floor(lat/5), floor(lon/10))].add(group)
            qualifying_site_years[group].add((arr, site, year))
    if rows == 0 or not by_group:
        raise ValueError("empty qualified metadata geometry")
    both = sum(len(v) == 2 for v in shared_grids.values())
    return {
        "cohort": cohort,
        "file_id": spec["file_id"],
        "verified_sha256": spec["sha256"],
        "rows": rows,
        "headers": sorted(set(reader.fieldnames or ())),
        "development_levels": dict(sorted(by_level.items())),
        "qualified_development_groups": dict(sorted(by_group.items())),
        "year_rows": dict(sorted(by_year.items())),
        "excluded_metadata": dict(sorted(excluded.items())),
        "distinct_deployment_ids": len(deployment_ids),
        "physical_site_years": len(sites),
        "physical_site_years_by_group": {
            g: len(qualifying_site_years[g]) for g in ("low", "high")
        },
        "distinct_array_by_group": {
            g: len({a for (a, label) in arrays if label == g})
            for g in ("low", "high")
        },
        "latitude_longitude_grid_cells_with_both_groups": both,
        "no_biological_sequence_records_opened": True,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--historical-deployments", type=Path, required=True)
    p.add_argument("--holdout-deployments", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = {
        "status": "E6_SNAPSHOT_RESPONSE_BLIND_DEPLOYMENT_GEOMETRY_ONLY",
        "history": audit_deployments(args.historical_deployments, "history"),
        "holdout_2024": audit_deployments(args.holdout_deployments, "holdout_2024"),
        "frozen_design": "docs/replication/E6_SNAPSHOT_URBAN_TEMPORAL_ASSEMBLY_FROZEN_DESIGN.md",
        "biological_sequence_files_opened": 0,
        "fit_count": 0,
        "e5_qualification_changed": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
