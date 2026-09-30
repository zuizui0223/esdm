#!/usr/bin/env python3
"""Build physical-location-block ODSP sensitivity bundles for frozen E4 MICA."""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

from esdm.transfer.e4_mica_odsp import _e4_mica_records
from esdm.transfer.odsp_adapter import (
    ODSPInformationLevel,
    build_odsp_transfer_bundle,
)


def _find(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name for name in archive.namelist()
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {basename!r}: {matches!r}")
    return matches[0]


def _location_map(archive_path: Path) -> dict[str, str]:
    with zipfile.ZipFile(archive_path) as archive:
        rows = list(csv.DictReader(io.StringIO(
            archive.read(_find(archive, "deployments.csv")).decode("utf-8-sig")
        )))
    output = {}
    for row in rows:
        deployment_id = str(row.get("deploymentID", "")).strip()
        location = str(row.get("locationName", "")).strip()
        if not deployment_id:
            raise ValueError("empty deploymentID in frozen MICA archive")
        if not location:
            raise ValueError(f"deployment {deployment_id!r} lacks locationName")
        output[deployment_id] = location
    return output


def _records(result, locations):
    records, _git_sha = _e4_mica_records(result)
    output = []
    for row in records:
        deployment_id = str(row["deploymentID"])
        if deployment_id not in locations:
            raise ValueError(f"heldout deployment missing locationName: {deployment_id}")
        output.append({**row, "physical_location": locations[deployment_id]})
    if len(output) != 733:
        raise ValueError("location-block sensitivity requires 733 heldout rows")
    if len({row["physical_location"] for row in output}) != 27:
        raise ValueError("location-block sensitivity requires 27 physical locations")
    return output


def _bundle(records, *, axis):
    if axis == "activity":
        levels = (
            ODSPInformationLevel(
                name="suitability_state",
                information=("suitability", "state"),
                source_score_field="activity_knockout_heldout_log_score",
            ),
            ODSPInformationLevel(
                name="suitability_state_activity",
                information=("suitability", "state", "activity"),
                source_score_field="full_heldout_log_score",
            ),
        )
    elif axis == "state":
        levels = (
            ODSPInformationLevel(
                name="suitability_activity",
                information=("suitability", "activity"),
                source_score_field="state_knockout_heldout_log_score",
            ),
            ODSPInformationLevel(
                name="suitability_activity_state",
                information=("suitability", "activity", "state"),
                source_score_field="full_heldout_log_score",
            ),
        )
    else:
        raise ValueError("axis must be activity or state")

    return build_odsp_transfer_bundle(
        endpoint_id=f"esdm_e4_mica_{axis}_location_block_sensitivity_v1",
        levels=levels,
        records=records,
        group_field="endpoint_group",
        row_id_field="deploymentID",
        block_field="physical_location",
        analysis_mode="descriptive",
        filtration_frozen_before_outcome_scoring=True,
        source_schema="e4-mica-exact-sparse-result-v1",
        source_git_sha=None,
        group_semantics=(
            "single terminal E4 MICA endpoint; 27 physical locationName values are "
            "post-result sensitivity resampling blocks; deployment-level frozen "
            "point scores remain unchanged"
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    records = _records(result, _location_map(args.archive))
    activity = _bundle(records, axis="activity")
    state = _bundle(records, axis="state")

    payload = {
        "row_count": len(records),
        "physical_location_block_count": len(
            {row["physical_location"] for row in records}
        ),
        "activity": activity.write(args.out_dir / "activity"),
        "state": state.write(args.out_dir / "state"),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
