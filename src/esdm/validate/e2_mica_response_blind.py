"""Response-blind E2 MICA deployment/header qualification.

This module may inspect:
- archive entry names;
- datapackage metadata if present;
- full deployments rows;
- the observations CSV header line only.

It must not inspect observations data rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
from typing import Mapping
import zipfile


STREAM_SALT = "esdm-e2-r5b-stream-v1|"
REQUIRED_DEPLOYMENT_COLUMNS = (
    "deploymentID",
    "latitude",
    "longitude",
    "deploymentStart",
    "deploymentEnd",
)
REQUIRED_OBSERVATION_COLUMNS = (
    "observationID",
    "deploymentID",
    "eventID",
    "eventStart",
    "observationLevel",
    "observationType",
    "scientificName",
    "count",
)
MIN_TRAINING_DEPLOYMENTS = 50
MIN_HELDOUT_DEPLOYMENTS = 12
MIN_ROLE_COUNT = 8


@dataclass(frozen=True, slots=True)
class DeploymentRecord:
    deployment_id: str
    latitude: float
    longitude: float
    deployment_start: str
    deployment_end: str


@dataclass(frozen=True, slots=True)
class EastHoldout:
    west_training_longitude: float
    east_heldout_longitude: float
    longitude_gap: float
    training_ids: tuple[str, ...]
    heldout_ids: tuple[str, ...]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _parse_datetime(value: str, *, name: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{name} is not ISO-8601 parseable: {text!r}") from exc


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


def _read_observation_header(
    archive: zipfile.ZipFile,
    entry: str,
    *,
    max_bytes: int,
) -> tuple[str, ...]:
    if max_bytes < 64:
        raise ValueError("observations header byte limit is implausibly small")
    with archive.open(entry, "r") as handle:
        line = handle.readline(max_bytes + 1)
    if len(line) > max_bytes:
        raise ValueError("observations header exceeds frozen byte limit")
    if not line.endswith((b"\n", b"\r")):
        raise ValueError("observations header newline not found within frozen byte limit")
    text = line.decode("utf-8-sig").rstrip("\r\n")
    row = next(csv.reader([text]))
    columns = tuple(value.strip() for value in row)
    if not columns or any(not value for value in columns):
        raise ValueError("observations header contains empty column names")
    if len(set(columns)) != len(columns):
        raise ValueError("observations header contains duplicate column names")
    return columns


def _read_deployments(
    archive: zipfile.ZipFile,
    entry: str,
) -> tuple[tuple[str, ...], tuple[DeploymentRecord, ...], str]:
    payload = archive.read(entry)
    payload_sha256 = _sha256_bytes(payload)
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("deployments CSV has no header")
    columns = tuple(str(value).strip() for value in reader.fieldnames)
    missing = [value for value in REQUIRED_DEPLOYMENT_COLUMNS if value not in columns]
    if missing:
        raise ValueError(f"deployment file missing required columns: {missing!r}")

    records: list[DeploymentRecord] = []
    seen: set[str] = set()
    for index, row in enumerate(reader):
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id or deployment_id in seen:
            raise ValueError("deploymentID values must be unique non-empty strings")
        seen.add(deployment_id)
        try:
            latitude = float(str(row.get("latitude", "")).strip())
            longitude = float(str(row.get("longitude", "")).strip())
        except ValueError as exc:
            raise ValueError(f"deployment row {index} has non-numeric coordinates") from exc
        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            raise ValueError(f"deployment row {index} has invalid latitude")
        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            raise ValueError(f"deployment row {index} has invalid longitude")
        start = str(row.get("deploymentStart", "")).strip()
        end = str(row.get("deploymentEnd", "")).strip()
        start_dt = _parse_datetime(start, name=f"deployments[{index}].deploymentStart")
        end_dt = _parse_datetime(end, name=f"deployments[{index}].deploymentEnd")
        if end_dt < start_dt:
            raise ValueError(f"deployment row {index} ends before it starts")
        records.append(
            DeploymentRecord(
                deployment_id=deployment_id,
                latitude=latitude,
                longitude=longitude,
                deployment_start=start,
                deployment_end=end,
            )
        )
    if not records:
        raise ValueError("deployments CSV is empty")
    return columns, tuple(records), payload_sha256


def _select_east_holdout(records: tuple[DeploymentRecord, ...]) -> EastHoldout:
    by_longitude: dict[float, list[str]] = {}
    for record in records:
        by_longitude.setdefault(record.longitude, []).append(record.deployment_id)
    longitudes = sorted(by_longitude)
    if len(longitudes) < 2:
        raise ValueError("at least two distinct deployment longitudes are required")

    candidates: list[tuple[float, float, float, tuple[str, ...], tuple[str, ...]]] = []
    for west, east in zip(longitudes, longitudes[1:]):
        training = tuple(
            sorted(
                record.deployment_id
                for record in records
                if record.longitude <= west
            )
        )
        heldout = tuple(
            sorted(
                record.deployment_id
                for record in records
                if record.longitude >= east
            )
        )
        if (
            len(training) >= MIN_TRAINING_DEPLOYMENTS
            and len(heldout) >= MIN_HELDOUT_DEPLOYMENTS
        ):
            candidates.append((east - west, west, east, training, heldout))
    if not candidates:
        raise ValueError(
            "no strict east holdout satisfies frozen training/heldout deployment minima"
        )

    # Largest longitude gap; exact ties choose the easternmost cut.
    gap, west, east, training, heldout = max(
        candidates,
        key=lambda row: (row[0], row[1]),
    )
    if not west < east:
        raise AssertionError("selected east holdout is not strict")
    return EastHoldout(
        west_training_longitude=float(west),
        east_heldout_longitude=float(east),
        longitude_gap=float(gap),
        training_ids=training,
        heldout_ids=heldout,
    )


def _stream_role(deployment_id: str) -> str:
    digest = hashlib.sha256(
        (STREAM_SALT + deployment_id).encode("utf-8")
    ).digest()
    value = digest[0]
    if value <= 63:
        return "opportunistic_presence"
    if value <= 127:
        return "calibrated_presence"
    if value <= 207:
        return "state_annotated"
    return "state_calibration"


def _role_assignment(training_ids: tuple[str, ...]) -> tuple[dict[str, str], dict[str, int]]:
    assignment = {
        deployment_id: _stream_role(deployment_id)
        for deployment_id in training_ids
    }
    counts = {
        role: sum(value == role for value in assignment.values())
        for role in (
            "opportunistic_presence",
            "calibrated_presence",
            "state_annotated",
            "state_calibration",
        )
    }
    if any(value < MIN_ROLE_COUNT for value in counts.values()):
        raise ValueError(
            f"training stream role minimum failed: {counts!r}; "
            f"each role requires at least {MIN_ROLE_COUNT}"
        )
    return assignment, counts


def qualify_e2_mica_archive(
    archive_path: str | Path,
    *,
    observations_header_max_bytes: int = 16384,
) -> dict[str, object]:
    path = Path(archive_path)
    archive_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    with zipfile.ZipFile(path) as archive:
        deployments_entry = _find_unique_entry(archive, "deployments.csv")
        observations_entry = _find_unique_entry(archive, "observations.csv")
        datapackage_matches = [
            name
            for name in archive.namelist()
            if PurePosixPath(name).name == "datapackage.json"
            and not name.endswith("/")
        ]
        if len(datapackage_matches) > 1:
            raise ValueError("archive contains multiple datapackage.json entries")

        deployment_columns, records, deployments_sha256 = _read_deployments(
            archive,
            deployments_entry,
        )
        observation_columns = _read_observation_header(
            archive,
            observations_entry,
            max_bytes=observations_header_max_bytes,
        )
        missing_observation = [
            value
            for value in REQUIRED_OBSERVATION_COLUMNS
            if value not in observation_columns
        ]
        if missing_observation:
            raise ValueError(
                f"observations header missing required columns: {missing_observation!r}"
            )

        datapackage_sha256 = None
        if datapackage_matches:
            datapackage_sha256 = _sha256_bytes(
                archive.read(datapackage_matches[0])
            )

    holdout = _select_east_holdout(records)
    assignment, role_counts = _role_assignment(holdout.training_ids)

    manifest = {
        "training_deployment_ids": list(holdout.training_ids),
        "heldout_deployment_ids": list(holdout.heldout_ids),
        "training_role_by_deployment": {
            key: assignment[key]
            for key in sorted(assignment)
        },
        "heldout_role": "state_annotated_only",
    }

    return {
        "schema_version": 1,
        "result_id": "e2-mica-muskrat-response-blind-geometry-header-v1",
        "status": "RESPONSE_BLIND_GEOMETRY_HEADER_PASS",
        "candidate_id": "MICA_MUSKRAT",
        "archive": {
            "sha256": archive_sha256,
            "deployments_entry": deployments_entry,
            "observations_entry": observations_entry,
            "datapackage_sha256": datapackage_sha256,
            "deployments_sha256": deployments_sha256,
        },
        "schema": {
            "deployment_columns": list(deployment_columns),
            "observation_header_columns": list(observation_columns),
            "required_deployment_columns_present": True,
            "required_observation_columns_present": True,
        },
        "geometry": {
            "deployment_count": len(records),
            "training_deployment_count": len(holdout.training_ids),
            "heldout_deployment_count": len(holdout.heldout_ids),
            "max_training_longitude": holdout.west_training_longitude,
            "min_heldout_longitude": holdout.east_heldout_longitude,
            "longitude_gap": holdout.longitude_gap,
            "strict_east_extrapolation": (
                holdout.west_training_longitude < holdout.east_heldout_longitude
            ),
        },
        "roles": {
            "minimum_each_training_role": MIN_ROLE_COUNT,
            "training_counts": role_counts,
            "all_minima_pass": all(
                value >= MIN_ROLE_COUNT for value in role_counts.values()
            ),
            "heldout_role": "state_annotated_only",
            "direct_state_calibration_heldout_exposure": 0,
        },
        "manifest": manifest,
        "fingerprints": {
            "training_ids_sha256": _canonical_sha256(
                list(holdout.training_ids)
            ),
            "heldout_ids_sha256": _canonical_sha256(
                list(holdout.heldout_ids)
            ),
            "training_role_map_sha256": _canonical_sha256(
                manifest["training_role_by_deployment"]
            ),
            "manifest_sha256": _canonical_sha256(manifest),
            "observation_header_sha256": _canonical_sha256(
                list(observation_columns)
            ),
        },
        "response_boundary": {
            "observations_data_rows_read": 0,
            "scientific_name_values_read": False,
            "count_values_read": False,
            "state_values_read": False,
            "taxon_frequencies_computed": False,
            "focal_event_counts_computed": False,
            "model_fits": 0,
            "heldout_scores": 0,
            "authorizes_temporal_opening": False,
            "authorizes_full_response_opening": False,
        },
    }
