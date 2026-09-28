"""Metadata-only preflight utilities for the E3 MICA exploratory programme."""
from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile


REQUIRED_DEPLOYMENT_COLUMNS = (
    "deploymentID",
    "deploymentStart",
    "deploymentEnd",
)


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_datetime(value: str, *, name: str) -> datetime:
    text = str(value).strip()
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


def audit_nonpositive_deployment_durations(
    archive_path: str | Path,
) -> dict[str, object]:
    """Audit all deployment intervals without opening observation rows."""
    path = Path(archive_path)
    source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        entry = _find_unique_entry(archive, "deployments.csv")
        payload = archive.read(entry)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    fields = tuple(reader.fieldnames or ())
    missing = [name for name in REQUIRED_DEPLOYMENT_COLUMNS if name not in fields]
    if missing:
        raise ValueError(f"deployments.csv missing required columns: {missing!r}")

    seen: set[str] = set()
    excluded: list[dict[str, object]] = []
    row_count = 0
    negative_count = 0
    zero_count = 0
    for index, row in enumerate(reader, start=2):
        row_count += 1
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id or deployment_id in seen:
            raise ValueError("deploymentID values must be unique non-empty strings")
        seen.add(deployment_id)
        start = _parse_datetime(
            row.get("deploymentStart", ""),
            name=f"deployments[{index}].deploymentStart",
        )
        end = _parse_datetime(
            row.get("deploymentEnd", ""),
            name=f"deployments[{index}].deploymentEnd",
        )
        duration_seconds = (end - start).total_seconds()
        if duration_seconds <= 0.0:
            if duration_seconds < 0.0:
                negative_count += 1
            else:
                zero_count += 1
            excluded.append(
                {
                    "deploymentID": deployment_id,
                    "duration_seconds": duration_seconds,
                    "longitude": str(row.get("longitude", "")).strip(),
                    "latitude": str(row.get("latitude", "")).strip(),
                }
            )

    excluded_ids = sorted(row["deploymentID"] for row in excluded)
    return {
        "source_sha256": source_sha256,
        "deployment_row_count": row_count,
        "nonpositive_duration_count": len(excluded),
        "negative_duration_count": negative_count,
        "zero_duration_count": zero_count,
        "excluded_deployment_ids": excluded_ids,
        "excluded_deployment_ids_sha256": _canonical_sha256(excluded_ids),
        "excluded_deployments": excluded,
        "observations_data_rows_read": 0,
        "scientific_name_values_read": False,
        "count_values_read": False,
        "state_values_read": False,
    }


def sanitize_archive_by_deployment_ids(
    source_archive: str | Path,
    output_archive: str | Path,
    *,
    excluded_deployment_ids: set[str] | frozenset[str],
) -> dict[str, object]:
    """Remove excluded deployments and their observation rows using deploymentID only."""
    source = Path(source_archive)
    output = Path(output_archive)
    excluded = frozenset(str(value) for value in excluded_deployment_ids)
    if not excluded:
        raise ValueError("E3 sanitization requires at least one frozen excluded deployment")

    removed_deployments = 0
    removed_observation_rows = 0
    retained_observation_rows = 0
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as src, zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED
    ) as dst:
        deployments_entry = _find_unique_entry(src, "deployments.csv")
        observations_entry = _find_unique_entry(src, "observations.csv")

        for info in src.infolist():
            if info.is_dir():
                dst.writestr(info, b"")
                continue
            raw = src.read(info.filename)
            if info.filename == deployments_entry:
                reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
                if "deploymentID" not in tuple(reader.fieldnames or ()):
                    raise ValueError("deployments.csv lacks deploymentID")
                out = io.StringIO(newline="")
                writer = csv.DictWriter(out, fieldnames=list(reader.fieldnames or ()))
                writer.writeheader()
                for row in reader:
                    if str(row.get("deploymentID", "")).strip() in excluded:
                        removed_deployments += 1
                        continue
                    writer.writerow(row)
                raw = out.getvalue().encode("utf-8")
            elif info.filename == observations_entry:
                reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
                if "deploymentID" not in tuple(reader.fieldnames or ()):
                    raise ValueError("observations.csv lacks deploymentID")
                out = io.StringIO(newline="")
                writer = csv.DictWriter(out, fieldnames=list(reader.fieldnames or ()))
                writer.writeheader()
                for row in reader:
                    deployment_id = str(row.get("deploymentID", "")).strip()
                    if deployment_id in excluded:
                        removed_observation_rows += 1
                        continue
                    retained_observation_rows += 1
                    writer.writerow(row)
                raw = out.getvalue().encode("utf-8")
            dst.writestr(info, raw)

    return {
        "excluded_deployment_ids": sorted(excluded),
        "excluded_deployment_ids_sha256": _canonical_sha256(sorted(excluded)),
        "removed_deployment_rows": removed_deployments,
        "removed_observation_rows": removed_observation_rows,
        "retained_observation_rows": retained_observation_rows,
        "row_filter_uses_only_deployment_id": True,
        "sanitized_archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
