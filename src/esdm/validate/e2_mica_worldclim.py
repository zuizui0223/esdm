"""Response-blind WorldClim BIO12 freeze for the E2 MICA candidate."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import tempfile
from typing import Mapping
import zipfile

from .e2_mica_response_blind import qualify_e2_mica_archive


WORLDCLIM_MEMBER = "wc2.1_10m_bio_12.tif"


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _find_unique_entry(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"archive must contain exactly one {basename!r}; observed {matches!r}"
        )
    return matches[0]


def _compare_response_blind(
    observed: Mapping[str, object],
    frozen: Mapping[str, object],
) -> None:
    result = frozen["result"]
    if observed["status"] != "RESPONSE_BLIND_GEOMETRY_HEADER_PASS":
        raise ValueError("recomputed response-blind qualification did not pass")
    if observed["archive"]["sha256"] != result["archive_sha256"]:
        raise ValueError("response-blind archive sha256 mismatch")
    if observed["archive"]["deployments_sha256"] != result["deployments_sha256"]:
        raise ValueError("response-blind deployments sha256 mismatch")
    if observed["geometry"]["deployment_count"] != result["deployment_count"]:
        raise ValueError("response-blind deployment count mismatch")
    if (
        observed["geometry"]["training_deployment_count"]
        != result["training_deployment_count"]
    ):
        raise ValueError("response-blind training count mismatch")
    if (
        observed["geometry"]["heldout_deployment_count"]
        != result["heldout_deployment_count"]
    ):
        raise ValueError("response-blind heldout count mismatch")
    for name, expected in result["fingerprints"].items():
        if observed["fingerprints"].get(name) != expected:
            raise ValueError(f"response-blind fingerprint mismatch: {name}")


def _deployment_coordinates(
    archive: zipfile.ZipFile,
    entry: str,
) -> dict[str, tuple[float, float]]:
    payload = archive.read(entry).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(payload))
    required = {"deploymentID", "latitude", "longitude"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError("deployments CSV lacks climate geometry columns")

    output: dict[str, tuple[float, float]] = {}
    for index, row in enumerate(reader):
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id:
            raise ValueError(f"deployments[{index}] has empty deploymentID")
        try:
            latitude = float(str(row.get("latitude", "")).strip())
            longitude = float(str(row.get("longitude", "")).strip())
        except ValueError as exc:
            raise ValueError(
                f"deployments[{index}] has non-numeric coordinates"
            ) from exc
        if not math.isfinite(latitude) or not -90.0 <= latitude <= 90.0:
            raise ValueError(f"deployments[{index}] has invalid latitude")
        if not math.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError(f"deployments[{index}] has invalid longitude")
        if deployment_id in output:
            raise ValueError("deploymentID values must be unique")
        output[deployment_id] = (latitude, longitude)
    return output


def freeze_e2_mica_worldclim(
    mica_archive_path: str | Path,
    worldclim_archive_path: str | Path,
    response_blind_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Freeze BIO12 values without reading MICA observation data rows."""

    import rasterio

    mica_path = Path(mica_archive_path)
    climate_path = Path(worldclim_archive_path)

    recomputed = qualify_e2_mica_archive(mica_path)
    _compare_response_blind(recomputed, response_blind_receipt)

    with zipfile.ZipFile(mica_path) as archive:
        deployments_entry = _find_unique_entry(archive, "deployments.csv")
        coordinates = _deployment_coordinates(archive, deployments_entry)

    training_ids = tuple(recomputed["manifest"]["training_deployment_ids"])
    heldout_ids = tuple(recomputed["manifest"]["heldout_deployment_ids"])
    expected_ids = set(training_ids) | set(heldout_ids)
    if set(coordinates) != expected_ids:
        raise ValueError("deployment coordinate IDs do not match frozen partition")

    worldclim_bytes = climate_path.read_bytes()
    worldclim_archive_sha256 = hashlib.sha256(worldclim_bytes).hexdigest()
    with zipfile.ZipFile(io.BytesIO(worldclim_bytes)) as archive:
        names = set(archive.namelist())
        if WORLDCLIM_MEMBER not in names:
            raise ValueError(f"WorldClim archive missing {WORLDCLIM_MEMBER!r}")
        raster_bytes = archive.read(WORLDCLIM_MEMBER)
    raster_sha256 = hashlib.sha256(raster_bytes).hexdigest()

    ordered_ids = tuple(sorted(coordinates))
    with tempfile.TemporaryDirectory() as tmpdir:
        tif = Path(tmpdir) / WORLDCLIM_MEMBER
        tif.write_bytes(raster_bytes)
        with rasterio.open(tif) as dataset:
            if dataset.crs is None or str(dataset.crs).upper() not in {
                "EPSG:4326",
                "OGC:CRS84",
            }:
                raise ValueError(f"unexpected WorldClim CRS {dataset.crs!r}")
            samples = [
                float(value[0])
                for value in dataset.sample(
                    [
                        (coordinates[deployment_id][1], coordinates[deployment_id][0])
                        for deployment_id in ordered_ids
                    ]
                )
            ]
            nodata = dataset.nodata

    if len(samples) != len(ordered_ids):
        raise ValueError("WorldClim sample count mismatch")

    training_set = set(training_ids)
    rows = []
    for deployment_id, bio12 in zip(ordered_ids, samples, strict=True):
        if not math.isfinite(bio12):
            raise ValueError(f"non-finite BIO12 for {deployment_id!r}")
        if nodata is not None and bio12 == float(nodata):
            raise ValueError(f"nodata BIO12 for {deployment_id!r}")
        latitude, longitude = coordinates[deployment_id]
        rows.append(
            {
                "deploymentID": deployment_id,
                "latitude": latitude,
                "longitude": longitude,
                "partition": (
                    "training"
                    if deployment_id in training_set
                    else "heldout"
                ),
                "bio12_mm": bio12,
            }
        )

    training_values = [
        row["bio12_mm"] for row in rows if row["partition"] == "training"
    ]
    mean = math.fsum(training_values) / len(training_values)
    variance = math.fsum(
        (value - mean) ** 2 for value in training_values
    ) / len(training_values)
    sd = math.sqrt(variance)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("training BIO12 has no positive finite variation")

    for row in rows:
        row["precip_z_train"] = (row["bio12_mm"] - mean) / sd

    canonical_rows = sorted(rows, key=lambda row: row["deploymentID"])
    return {
        "schema_version": 1,
        "result_id": "e2-mica-worldclim-bio12-v1",
        "status": "CLIMATE_QUALIFIED",
        "candidate_id": "MICA_MUSKRAT",
        "source_reverification": {
            "archive_sha256": recomputed["archive"]["sha256"],
            "deployments_sha256": recomputed["archive"]["deployments_sha256"],
            "fingerprints": recomputed["fingerprints"],
        },
        "worldclim": {
            "archive_sha256": worldclim_archive_sha256,
            "bio12_raster_sha256": raster_sha256,
            "member": WORLDCLIM_MEMBER,
            "units": "mm",
        },
        "training": {
            "deployment_count": len(training_ids),
            "bio12_mean_mm": mean,
            "bio12_population_sd_mm": sd,
        },
        "heldout_deployment_count": len(heldout_ids),
        "deployment_climate_sha256": _canonical_sha256(canonical_rows),
        "deployment_climate": canonical_rows,
        "response_firewall": {
            "scientific_name_values_read": False,
            "count_values_read": False,
            "observation_rows_read_for_climate": 0,
            "focal_taxon_filtering": False,
            "model_fits": 0,
            "heldout_scores": 0,
            "full_response_opened": False,
        },
        "decision": {
            "climate_qualified": True,
            "authorizes_full_response": False,
            "requires_separate_full_response_authorization": True,
        },
    }
