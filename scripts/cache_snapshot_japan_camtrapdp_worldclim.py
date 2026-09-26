#!/usr/bin/env python3
"""Freeze Snapshot Japan WorldClim BIO12 before any Camtrap DP response access."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_JAPAN_CAMTRAPDP_CLIMATE_CONTRACT.json"
OUTPUT = ROOT / "artifacts" / "snapshot_japan_camtrapdp_climate.json"


def _get(url: str, user_agent: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
        return response.read()


def _md5(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()  # noqa: S324 provenance only


def main() -> int:
    import rasterio

    cfg = json.loads(CONTRACT.read_text(encoding="utf-8"))
    output = OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema": "esdm.empirical_r5b.snapshot_japan_camtrapdp_climate_result.v1",
        "status": "STOP_PRE_RESPONSE_CLIMATE_TRANSPORT_OR_SCHEMA",
        "camtrapdp_archive_requests": 0,
        "camtrapdp_response_bytes_opened": 0,
        "camtrapdp_response_rows_opened": 0,
        "camtrapdp_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0
    }
    try:
        geometry_cfg = cfg["safe_geometry_source"]
        deployment_bytes = _get(
            geometry_cfg["url"],
            "esdm-r5b-snapshot-japan-worldclim-geometry/1.0",
        )
        if _md5(deployment_bytes) != geometry_cfg["md5"]:
            raise RuntimeError("safe deployment MD5 drift")

        reader = csv.DictReader(io.StringIO(deployment_bytes.decode("utf-8-sig")))
        required = {"deployment_id", "latitude", "longitude"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise RuntimeError(f"safe deployment schema missing {sorted(missing)}")
        rows = list(reader)
        if len(rows) != int(geometry_cfg["expected_rows"]):
            raise RuntimeError(f"safe deployment row drift: {len(rows)}")

        cameras = []
        seen_coordinates = set()
        for index, row in enumerate(rows):
            deployment_id = str(row["deployment_id"]).strip()
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])
            if not deployment_id:
                raise RuntimeError(f"empty deployment_id at row {index}")
            if not (math.isfinite(latitude) and math.isfinite(longitude)):
                raise RuntimeError(f"non-finite coordinate at row {index}")
            coord = (latitude, longitude)
            seen_coordinates.add(coord)
            partition = (
                "training"
                if longitude < float(geometry_cfg["east_holdout_threshold_longitude"])
                else "heldout"
                if longitude > float(geometry_cfg["east_holdout_threshold_longitude"])
                else "boundary"
            )
            if partition == "boundary":
                raise RuntimeError("deployment lies exactly on frozen east threshold")
            cameras.append({
                "deployment_id": deployment_id,
                "latitude": latitude,
                "longitude": longitude,
                "partition": partition,
            })
        if len(seen_coordinates) != int(geometry_cfg["expected_unique_coordinates"]):
            raise RuntimeError("safe deployment unique-coordinate drift")
        train = [row for row in cameras if row["partition"] == "training"]
        heldout = [row for row in cameras if row["partition"] == "heldout"]
        if len(train) != int(geometry_cfg["expected_training_count"]):
            raise RuntimeError(f"training count drift: {len(train)}")
        if len(heldout) != int(geometry_cfg["expected_heldout_count"]):
            raise RuntimeError(f"heldout count drift: {len(heldout)}")

        climate_cfg = cfg["climate_source"]
        climate_bytes = _get(
            climate_cfg["archive_url"],
            "esdm-r5b-snapshot-japan-worldclim/1.0",
        )
        archive_sha256 = hashlib.sha256(climate_bytes).hexdigest()
        with zipfile.ZipFile(io.BytesIO(climate_bytes)) as archive:
            names = set(archive.namelist())
            member = str(climate_cfg["member"])
            if member not in names:
                raise RuntimeError(f"WorldClim archive missing {member!r}")
            raster_bytes = archive.read(member)
        raster_sha256 = hashlib.sha256(raster_bytes).hexdigest()

        with tempfile.TemporaryDirectory() as tmpdir:
            tif = Path(tmpdir) / Path(climate_cfg["member"]).name
            tif.write_bytes(raster_bytes)
            with rasterio.open(tif) as dataset:
                if dataset.crs is None or str(dataset.crs).upper() not in {"EPSG:4326", "OGC:CRS84"}:
                    raise RuntimeError(f"unexpected WorldClim CRS {dataset.crs!r}")
                coordinates = [(row["longitude"], row["latitude"]) for row in cameras]
                samples = [float(value[0]) for value in dataset.sample(coordinates)]
                nodata = dataset.nodata

        if len(samples) != len(cameras):
            raise RuntimeError("WorldClim sample count mismatch")
        for row, value in zip(cameras, samples, strict=True):
            if not math.isfinite(value) or (nodata is not None and value == float(nodata)):
                raise RuntimeError(f"invalid BIO12 value for {row['deployment_id']!r}")
            row["bio12_mm"] = value

        training_values = [row["bio12_mm"] for row in cameras if row["partition"] == "training"]
        mean = math.fsum(training_values) / len(training_values)
        variance = math.fsum((value - mean) ** 2 for value in training_values) / len(training_values)
        sd = math.sqrt(variance)
        if not math.isfinite(sd) or sd <= 0.0:
            raise RuntimeError("training BIO12 has no positive finite variation")
        for row in cameras:
            row["precip_z_train"] = (row["bio12_mm"] - mean) / sd

        canonical = json.dumps(
            cameras,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        result = {
            **base,
            "status": "CLIMATE_QUALIFIED",
            "safe_deployment_md5": _md5(deployment_bytes),
            "safe_deployment_sha256": hashlib.sha256(deployment_bytes).hexdigest(),
            "worldclim_archive_sha256": archive_sha256,
            "worldclim_bio12_raster_sha256": raster_sha256,
            "training_bio12_mean_mm": mean,
            "training_bio12_population_sd_mm": sd,
            "camera_count": len(cameras),
            "training_count": len(train),
            "heldout_count": len(heldout),
            "camera_climate_sha256": hashlib.sha256(canonical).hexdigest(),
            "camera_climate": sorted(cameras, key=lambda row: row["deployment_id"]),
        }
    except Exception as exc:
        result = {
            **base,
            "reason": f"{type(exc).__name__}: {exc}"
        }

    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "status": result["status"],
        "camera_count": result.get("camera_count"),
        "reason": result.get("reason"),
        "camtrapdp_response_rows_opened": result["camtrapdp_response_rows_opened"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
