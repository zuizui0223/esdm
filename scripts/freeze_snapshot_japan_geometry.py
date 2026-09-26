#!/usr/bin/env python3
"""Freeze Snapshot Japan deployment geometry without opening response data."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_JAPAN_GEOMETRY_CONTRACT.json"
OUTPUT = ROOT / "artifacts" / "snapshot_japan_geometry.json"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "esdm-r5b-snapshot-japan-geometry/1.0"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:  # noqa: S310
        return response.read()


def _rows(raw: bytes):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return tuple(reader.fieldnames or ()), list(reader)


def _choose_east_cut(records):
    longitudes = sorted({float(row["longitude"]) for row in records})
    candidates = []
    for west, east in zip(longitudes, longitudes[1:], strict=True):
        train = [row for row in records if float(row["longitude"]) <= west]
        held = [row for row in records if float(row["longitude"]) >= east]
        if len(train) >= 50 and len(held) >= 12:
            candidates.append((east - west, west, east, len(train), len(held)))
    if not candidates:
        raise RuntimeError("no eligible strict east holdout gap")
    gap, west, east, n_train, n_held = max(
        candidates,
        key=lambda value: (value[0], value[1]),
    )
    threshold = (west + east) / 2.0
    return {
        "gap_degrees": gap,
        "train_max_longitude": west,
        "heldout_min_longitude": east,
        "threshold_longitude": threshold,
        "train_count": n_train,
        "heldout_count": n_held,
    }


def _digest_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _role_assignments(train_rows, held_rows):
    ordered = sorted(
        (str(row["deployment_id"]).strip() for row in train_rows),
        key=lambda value: (_digest_id(value), value),
    )
    n = len(ordered)
    n_presence = n // 2
    remaining = n - n_presence
    n_annotated = remaining // 2
    roles = {}
    for value in ordered[:n_presence]:
        roles[value] = "calibrated_presence"
    for value in ordered[n_presence:n_presence + n_annotated]:
        roles[value] = "state_annotated"
    for value in ordered[n_presence + n_annotated:]:
        roles[value] = "state_composition"
    for row in held_rows:
        roles[str(row["deployment_id"]).strip()] = "heldout_state_annotated"
    return roles


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    raw = _fetch(contract["dataset"]["deployment_url"])
    md5 = hashlib.md5(raw).hexdigest()  # noqa: S324 provenance only
    if md5 != contract["dataset"]["deployment_expected_md5"]:
        raise RuntimeError(f"deployment MD5 drift: {md5}")

    columns, rows = _rows(raw)
    required = {"deployment_id", "latitude", "longitude", "start_date", "end_date"}
    missing = required - set(columns)
    if missing:
        raise RuntimeError(f"deployment schema missing {sorted(missing)}")
    if len(rows) != int(contract["dataset"]["expected_deployments"]):
        raise RuntimeError(f"deployment row drift: {len(rows)}")

    ids = [str(row["deployment_id"]).strip() for row in rows]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise RuntimeError("deployment IDs must be unique and non-empty")

    coordinates = {
        (float(row["latitude"]), float(row["longitude"]))
        for row in rows
    }
    if len(coordinates) != int(contract["dataset"]["expected_unique_coordinates"]):
        raise RuntimeError("unique coordinate count drift")

    for row in rows:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if not (math.isfinite(lat) and math.isfinite(lon)):
            raise RuntimeError("non-finite deployment coordinate")

    cut = _choose_east_cut(rows)
    train = [
        row for row in rows
        if float(row["longitude"]) < cut["threshold_longitude"]
    ]
    held = [
        row for row in rows
        if float(row["longitude"]) > cut["threshold_longitude"]
    ]
    if len(train) != cut["train_count"] or len(held) != cut["heldout_count"]:
        raise RuntimeError("east holdout count mismatch")
    if min(float(row["longitude"]) for row in held) <= max(
        float(row["longitude"]) for row in train
    ):
        raise RuntimeError("east heldout is not strictly beyond training longitude")

    roles = _role_assignments(train, held)
    counts = {}
    for role in roles.values():
        counts[role] = counts.get(role, 0) + 1
    for role in ("calibrated_presence", "state_annotated", "state_composition"):
        if counts.get(role, 0) < int(
            contract["training_camera_roles"]["minimum_each_role"]
        ):
            raise RuntimeError(f"insufficient deployment count for {role}")

    geometry_rows = [
        {
            "deployment_id": str(row["deployment_id"]).strip(),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "start_date": str(row["start_date"]).strip(),
            "end_date": str(row["end_date"]).strip(),
            "role": roles[str(row["deployment_id"]).strip()],
        }
        for row in sorted(rows, key=lambda r: str(r["deployment_id"]))
    ]
    canonical = json.dumps(
        geometry_rows,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    payload = {
        "schema": "esdm.empirical_r5b.snapshot_japan_geometry_result.v1",
        "status": "GEOMETRY_QUALIFIED",
        "deployment_md5": md5,
        "deployment_sha256": hashlib.sha256(raw).hexdigest(),
        "deployment_count": len(rows),
        "unique_coordinate_count": len(coordinates),
        "east_holdout": cut,
        "role_counts": counts,
        "geometry_sha256": hashlib.sha256(canonical).hexdigest(),
        "geometry": geometry_rows,
        "response_payload_requests": 0,
        "response_header_requests": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
