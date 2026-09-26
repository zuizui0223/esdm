"""Response-blind Snapshot USA 2024 qualification for the frozen R5b empirical entry."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CONTRACT_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "empirical"
    / "SNAPSHOT_USA_2024_HEADER_CONTRACT.json"
)


@dataclass(frozen=True, slots=True)
class SnapshotUSASite:
    spatial_unit: str
    latitude: float
    longitude: float


def _contract() -> dict[str, object]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if value["contract_id"] != "empirical-r5b-snapshot-usa-2024-metadata-header-v1":
        raise ValueError("unexpected Snapshot USA header contract")
    if value["status"] != "FROZEN_PRE_RESPONSE_HEADER":
        raise ValueError("Snapshot USA header contract is not frozen pre-response")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stream_bucket(deployment_id: str) -> int:
    token = f"snapshot-usa-2024-r5b-stream-v1|{deployment_id}".encode("utf-8")
    return hashlib.sha256(token).digest()[0]


def _site_rank(spatial_unit: str) -> str:
    token = f"snapshot-usa-2024-r5b-v1|{spatial_unit}".encode("utf-8")
    return hashlib.sha256(token).hexdigest()


def _finite(value: str, *, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_int(value: str, *, name: str) -> int:
    try:
        result = int(float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _inclusive_nights(start: str, end: str) -> int:
    start_date = date.fromisoformat(str(start).strip())
    end_date = date.fromisoformat(str(end).strip())
    days = (end_date - start_date).days + 1
    if days <= 0:
        raise ValueError("deployment End_Date precedes Start_Date")
    return days


def parse_deployment_metadata(
    csv_bytes: bytes,
    *,
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    cfg = _contract() if contract is None else dict(contract)
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = tuple(cfg["required_deployment_columns"])
    header = tuple(reader.fieldnames or ())
    missing = [name for name in required if name not in header]
    if missing:
        raise ValueError(f"deployment file missing required columns: {missing}")

    rows = list(reader)
    if not rows:
        raise ValueError("deployment file contains no metadata rows")

    spatial_cfg = cfg["spatial_contract"]
    minimum_longitude = float(spatial_cfg["candidate_longitude_minimum"])
    target_n = int(spatial_cfg["selected_unique_sites"])

    site_coordinates: dict[str, tuple[float, float]] = {}
    site_deployments: dict[str, set[str]] = {}
    deployment_rows: dict[str, dict[str, object]] = {}

    for index, row in enumerate(rows):
        array = str(row.get("Camera_Trap_Array", "")).strip()
        site = str(row.get("Site_Name", "")).strip()
        deployment = str(row.get("Deployment_ID", "")).strip()
        if not array or not site or not deployment:
            continue

        latitude = _finite(row.get("Latitude", ""), name=f"row[{index}].Latitude")
        longitude = _finite(
            row.get("Longitude", ""), name=f"row[{index}].Longitude"
        )
        survey_nights = _positive_int(
            row.get("Survey_Nights", ""), name=f"row[{index}].Survey_Nights"
        )
        inclusive_nights = _inclusive_nights(
            row.get("Start_Date", ""),
            row.get("End_Date", ""),
        )
        active_fraction = survey_nights / inclusive_nights
        if not 0.0 < active_fraction <= 1.0:
            raise ValueError(
                f"row[{index}] reconstructed active fraction outside (0,1]: "
                f"{active_fraction}"
            )

        spatial_unit = f"{array}|{site}"
        coordinate = (latitude, longitude)
        prior = site_coordinates.get(spatial_unit)
        if prior is not None and (
            not math.isclose(prior[0], latitude, abs_tol=1e-10, rel_tol=0.0)
            or not math.isclose(prior[1], longitude, abs_tol=1e-10, rel_tol=0.0)
        ):
            raise ValueError(
                f"spatial unit {spatial_unit!r} has inconsistent coordinates"
            )
        site_coordinates[spatial_unit] = coordinate
        site_deployments.setdefault(spatial_unit, set()).add(deployment)

        prior_deployment = deployment_rows.get(deployment)
        current = {
            "spatial_unit": spatial_unit,
            "latitude": latitude,
            "longitude": longitude,
            "survey_nights": survey_nights,
            "inclusive_nights": inclusive_nights,
            "active_fraction": active_fraction,
            "start_date": str(row["Start_Date"]).strip(),
            "end_date": str(row["End_Date"]).strip(),
        }
        if prior_deployment is not None and prior_deployment != current:
            raise ValueError(
                f"Deployment_ID {deployment!r} maps to inconsistent metadata"
            )
        deployment_rows[deployment] = current

    eligible_sites = [
        SnapshotUSASite(spatial_unit, lat, lon)
        for spatial_unit, (lat, lon) in site_coordinates.items()
        if lon >= minimum_longitude
    ]
    if len(eligible_sites) < target_n:
        raise ValueError(
            f"only {len(eligible_sites)} eligible unique sites; need {target_n}"
        )

    selected = sorted(
        eligible_sites,
        key=lambda row: (_site_rank(row.spatial_unit), row.spatial_unit),
    )[:target_n]

    target_holdout = int(math.ceil(
        float(spatial_cfg["east_holdout_fraction_target"]) * len(selected)
    ))
    ordered_east = sorted(
        selected,
        key=lambda row: (row.longitude, row.spatial_unit),
    )
    initial_holdout = ordered_east[-target_holdout:]
    boundary = min(row.longitude for row in initial_holdout)
    heldout = tuple(
        row for row in selected if row.longitude >= boundary
    )
    training = tuple(
        row for row in selected if row.longitude < boundary
    )
    if not training or not heldout:
        raise ValueError("east holdout produced an empty training or heldout set")
    if not max(row.longitude for row in training) < min(
        row.longitude for row in heldout
    ):
        raise ValueError("east holdout lacks strict longitude separation")

    training_units = {row.spatial_unit for row in training}
    heldout_units = {row.spatial_unit for row in heldout}

    training_deployments = sorted(
        deployment
        for deployment, meta in deployment_rows.items()
        if meta["spatial_unit"] in training_units
    )
    heldout_deployments = sorted(
        deployment
        for deployment, meta in deployment_rows.items()
        if meta["spatial_unit"] in heldout_units
    )
    if not training_deployments or not heldout_deployments:
        raise ValueError("selected sites contain no training or heldout deployments")

    stream_counts = {
        "opportunistic_presence": 0,
        "calibrated_presence": 0,
        "state_annotated": 0,
        "state_calibration": 0,
    }
    stream_by_deployment: dict[str, str] = {}
    for deployment in training_deployments:
        value = _stream_bucket(deployment)
        if value <= 63:
            stream = "opportunistic_presence"
        elif value <= 127:
            stream = "calibrated_presence"
        elif value <= 207:
            stream = "state_annotated"
        else:
            stream = "state_calibration"
        stream_counts[stream] += 1
        stream_by_deployment[deployment] = stream

    empty = [name for name, count in stream_counts.items() if count == 0]
    if empty:
        raise ValueError(f"training stream partition is empty: {empty}")

    return {
        "deployment_row_count": len(rows),
        "deployment_id_count": len(deployment_rows),
        "unique_spatial_unit_count": len(site_coordinates),
        "eligible_unique_site_count": len(eligible_sites),
        "selected_site_count": len(selected),
        "selected_spatial_units": sorted(row.spatial_unit for row in selected),
        "selected_sites": [
            {
                "spatial_unit": row.spatial_unit,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "partition": (
                    "training"
                    if row.spatial_unit in training_units
                    else "heldout"
                ),
            }
            for row in sorted(selected, key=lambda item: item.spatial_unit)
        ],
        "training_site_count": len(training),
        "heldout_site_count": len(heldout),
        "training_spatial_units": sorted(training_units),
        "heldout_spatial_units": sorted(heldout_units),
        "training_longitude_max": max(row.longitude for row in training),
        "heldout_longitude_min": min(row.longitude for row in heldout),
        "east_holdout_boundary_longitude": boundary,
        "training_deployment_count": len(training_deployments),
        "heldout_deployment_count": len(heldout_deployments),
        "training_stream_deployment_counts": stream_counts,
        "training_stream_by_deployment": stream_by_deployment,
        "heldout_deployments": heldout_deployments,
        "state_calibration_heldout_exposure": 0,
    }


def parse_sequence_header(
    header_bytes: bytes,
    *,
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    cfg = _contract() if contract is None else dict(contract)
    if b"\n" in header_bytes or b"\r" in header_bytes:
        header_bytes = header_bytes.splitlines(keepends=False)[0]
    if not header_bytes:
        raise ValueError("sequence header is empty")
    maximum = int(cfg["dataset"]["sequence_file"]["max_header_bytes"])
    if len(header_bytes) > maximum:
        raise ValueError("sequence header exceeds frozen maximum")
    text = header_bytes.decode("utf-8-sig").strip()
    header = tuple(next(csv.reader([text])))
    required = tuple(cfg["required_sequence_header_columns"])
    missing = [name for name in required if name not in header]
    if missing:
        raise ValueError(f"sequence header missing required columns: {missing}")
    return {
        "header_bytes": len(header_bytes),
        "header_sha256": _sha256(header_bytes),
        "columns": list(header),
        "required_columns_present": True,
        "response_rows_opened": 0,
        "response_values_opened": False,
    }


def _download_full(url: str, *, user_agent: str) -> bytes:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=90) as response:
        return response.read()


def _download_header_only(
    url: str,
    *,
    max_header_bytes: int,
    user_agent: str,
) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Range": f"bytes=0-{max_header_bytes - 1}",
        },
    )
    with urlopen(request, timeout=90) as response:
        line = response.readline(max_header_bytes + 1)
    if len(line) > max_header_bytes:
        raise ValueError("sequence header exceeds frozen maximum")
    if not line.endswith((b"\n", b"\r")):
        raise ValueError("sequence first line did not terminate within frozen header bytes")
    return line.rstrip(b"\r\n")


def run_snapshot_usa_metadata_header_gate() -> dict[str, object]:
    cfg = _contract()
    dataset = cfg["dataset"]
    base = {
        "schema": "esdm.empirical_r5b.snapshot_usa_2024_header.v1",
        "contract_id": cfg["contract_id"],
        "status": "STOP_PRE_RESPONSE_TRANSPORT",
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }

    try:
        deployment_bytes = _download_full(
            dataset["deployment_file"]["url"],
            user_agent="esdm-r5b-snapshot-usa-metadata/1.0",
        )
        deployment = parse_deployment_metadata(
            deployment_bytes,
            contract=cfg,
        )
        header_bytes = _download_header_only(
            dataset["sequence_file"]["url"],
            max_header_bytes=int(
                dataset["sequence_file"]["max_header_bytes"]
            ),
            user_agent="esdm-r5b-snapshot-usa-header/1.0",
        )
        header = parse_sequence_header(header_bytes, contract=cfg)
    except (HTTPError, URLError, TimeoutError) as exc:
        return {
            **base,
            "transport_error": f"{type(exc).__name__}: {exc}",
        }
    except Exception as exc:
        return {
            **base,
            "status": "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY",
            "qualification_error": f"{type(exc).__name__}: {exc}",
        }

    return {
        **base,
        "status": "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED",
        "transport_error": None,
        "deployment": {
            "file_name": dataset["deployment_file"]["name"],
            "bytes": len(deployment_bytes),
            "sha256": _sha256(deployment_bytes),
            **deployment,
        },
        "sequence_header": {
            "file_name": dataset["sequence_file"]["name"],
            **header,
        },
    }
