"""Frozen Daymet precipitation preprocessing for Snapshot USA empirical R5b."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
from typing import Iterable, Mapping
from urllib.parse import urlencode


CONTRACT_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "empirical"
    / "SNAPSHOT_USA_2024_DAYMET_PRECIPITATION_CONTRACT.json"
)


@dataclass(frozen=True, slots=True)
class DaymetSiteRequest:
    spatial_unit: str
    latitude: float
    longitude: float
    url: str
    cache_filename: str


def _contract() -> dict[str, object]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if value["contract_id"] != "empirical-r5b-snapshot-usa-2024-daymet-prcp-v1":
        raise ValueError("unexpected Snapshot USA precipitation contract")
    if value["status"] != "FROZEN_PRE_RESPONSE_CLIMATE":
        raise ValueError("Snapshot USA precipitation contract is not frozen")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finite(value: object, *, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _coordinate_text(value: float) -> str:
    return f"{float(value):.8f}"


def daymet_site_request(
    spatial_unit: str,
    latitude: float,
    longitude: float,
    *,
    contract: Mapping[str, object] | None = None,
) -> DaymetSiteRequest:
    cfg = _contract() if contract is None else dict(contract)
    spatial_unit = str(spatial_unit).strip()
    if not spatial_unit:
        raise ValueError("spatial_unit must be non-empty")
    latitude = _finite(latitude, name="latitude")
    longitude = _finite(longitude, name="longitude")

    lat_min, lat_max = (
        float(value) for value in cfg["eligibility"]["latitude_domain_required"]
    )
    lon_min, lon_max = (
        float(value) for value in cfg["eligibility"]["longitude_domain_required"]
    )
    if not lat_min <= latitude <= lat_max:
        raise ValueError(
            f"selected site {spatial_unit!r} latitude {latitude} outside frozen "
            f"Daymet single-pixel domain [{lat_min}, {lat_max}]"
        )
    if not lon_min <= longitude <= lon_max:
        raise ValueError(
            f"selected site {spatial_unit!r} longitude {longitude} outside frozen "
            f"Daymet single-pixel domain [{lon_min}, {lon_max}]"
        )

    tool = cfg["product"]["single_pixel_tool"]
    query = {
        "lat": _coordinate_text(latitude),
        "lon": _coordinate_text(longitude),
        **dict(tool["fixed_query_parameters"]),
    }
    url = f"{tool['api_base']}?{urlencode(query)}"
    cache_token = hashlib.sha256(spatial_unit.encode("utf-8")).hexdigest()[:20]
    return DaymetSiteRequest(
        spatial_unit=spatial_unit,
        latitude=latitude,
        longitude=longitude,
        url=url,
        cache_filename=f"{cache_token}.csv",
    )


def _find_daymet_header(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        try:
            columns = [value.strip().lower() for value in next(csv.reader([line]))]
        except Exception:
            continue
        if "year" in columns and "yday" in columns and any(
            value.startswith("prcp") for value in columns
        ):
            return index
    raise ValueError("Daymet response does not contain year/yday/prcp header")


def parse_daymet_prcp_response(
    raw_bytes: bytes,
    *,
    contract: Mapping[str, object] | None = None,
) -> dict[date, float]:
    cfg = _contract() if contract is None else dict(contract)
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Daymet response must be UTF-8 CSV text") from exc
    lines = text.splitlines()
    header_index = _find_daymet_header(lines)
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])))
    fieldnames = tuple(reader.fieldnames or ())
    lower = {name.strip().lower(): name for name in fieldnames}
    if "year" not in lower or "yday" not in lower:
        raise ValueError("Daymet header missing year or yday")
    prcp_candidates = [
        original
        for normalized, original in lower.items()
        if normalized.startswith("prcp")
    ]
    if len(prcp_candidates) != 1:
        raise ValueError("Daymet header must contain exactly one precipitation column")
    prcp_column = prcp_candidates[0]

    year_required = int(cfg["raw_cache_contract"]["year_required"])
    values: dict[int, float] = {}
    for row_index, row in enumerate(reader):
        if not row or all(not str(value or "").strip() for value in row.values()):
            continue
        try:
            year = int(str(row[lower["year"]]).strip())
            yday = int(str(row[lower["yday"]]).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Daymet row {row_index} has invalid year/yday"
            ) from exc
        if year != year_required:
            raise ValueError(
                f"Daymet response contains year {year}; expected only {year_required}"
            )
        if not 1 <= yday <= 365:
            raise ValueError(f"Daymet yday outside 1..365: {yday}")
        if yday in values:
            raise ValueError(f"duplicate Daymet yday: {yday}")
        raw_prcp = str(row.get(prcp_column, "") or "").strip()
        if raw_prcp.lower() in {"", "na", "nan", "null"}:
            raise ValueError(f"missing Daymet precipitation at yday {yday}")
        prcp = _finite(raw_prcp, name=f"prcp yday {yday}")
        if prcp < 0.0:
            raise ValueError(f"negative Daymet precipitation at yday {yday}")
        values[yday] = prcp

    expected = set(range(1, 366))
    if set(values) != expected:
        missing = sorted(expected - set(values))
        extra = sorted(set(values) - expected)
        raise ValueError(
            f"Daymet 2024 response must contain exact yday 1..365; "
            f"missing={missing[:10]}, extra={extra[:10]}"
        )

    origin = date(year_required, 1, 1)
    return {
        origin + timedelta(days=yday - 1): values[yday]
        for yday in range(1, 366)
    }


def cache_manifest_entry(
    request: DaymetSiteRequest,
    raw_bytes: bytes,
    *,
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    daily = parse_daymet_prcp_response(raw_bytes, contract=contract)
    precipitation = tuple(daily.values())
    return {
        "spatial_unit": request.spatial_unit,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "query_url": request.url,
        "cache_filename": request.cache_filename,
        "raw_bytes": len(raw_bytes),
        "raw_sha256": _sha256(raw_bytes),
        "daily_row_count": len(daily),
        "first_date": min(daily).isoformat(),
        "last_date": max(daily).isoformat(),
        "minimum_prcp_mm": min(precipitation),
        "maximum_prcp_mm": max(precipitation),
    }


def build_cache_manifest(
    requests: Iterable[DaymetSiteRequest],
    raw_by_spatial_unit: Mapping[str, bytes],
    *,
    contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    cfg = _contract() if contract is None else dict(contract)
    ordered = tuple(sorted(requests, key=lambda row: row.spatial_unit))
    if len(ordered) != int(cfg["eligibility"]["selected_site_count"]):
        raise ValueError(
            f"expected {cfg['eligibility']['selected_site_count']} selected sites, "
            f"observed {len(ordered)}"
        )
    if len({row.spatial_unit for row in ordered}) != len(ordered):
        raise ValueError("selected spatial units must be unique")
    missing = [
        row.spatial_unit
        for row in ordered
        if row.spatial_unit not in raw_by_spatial_unit
    ]
    extra = sorted(set(raw_by_spatial_unit) - {row.spatial_unit for row in ordered})
    if missing or extra:
        raise ValueError(
            f"Daymet cache coverage mismatch: missing={missing[:10]}, extra={extra[:10]}"
        )

    entries = [
        cache_manifest_entry(
            request,
            raw_by_spatial_unit[request.spatial_unit],
            contract=cfg,
        )
        for request in ordered
    ]
    core = {
        "schema": "esdm.empirical_snapshot_usa_daymet_cache.v1",
        "contract_id": cfg["contract_id"],
        "dataset_doi": cfg["product"]["dataset_doi"],
        "dataset_version": cfg["product"]["version"],
        "variable": cfg["product"]["variable"],
        "year": cfg["product"]["year"],
        "selected_site_count": len(entries),
        "entries": entries,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    canonical = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        **core,
        "manifest_sha256": _sha256(canonical),
    }


def iso_week_precipitation(
    daily_by_site: Mapping[str, Mapping[date, float]],
    contexts: Iterable[tuple[str, int, int]],
) -> dict[tuple[str, int, int], float]:
    result: dict[tuple[str, int, int], float] = {}
    for spatial_unit, iso_year, iso_week in contexts:
        key = (str(spatial_unit), int(iso_year), int(iso_week))
        if key in result:
            continue
        if key[0] not in daily_by_site:
            raise ValueError(f"missing Daymet daily series for {key[0]!r}")
        monday = date.fromisocalendar(key[1], key[2], 1)
        dates = tuple(monday + timedelta(days=offset) for offset in range(7))
        missing = [value for value in dates if value not in daily_by_site[key[0]]]
        if missing:
            raise ValueError(
                f"Daymet week {key[1]}-W{key[2]:02d} for {key[0]!r} "
                f"is missing dates: {[value.isoformat() for value in missing]}"
            )
        result[key] = math.fsum(
            float(daily_by_site[key[0]][value]) for value in dates
        )
    return result


def standardize_weekly_precipitation(
    weekly_mm: Mapping[tuple[str, int, int], float],
    training_positive_effort_contexts: Iterable[tuple[str, int, int]],
) -> dict[str, object]:
    training_keys = tuple(dict.fromkeys(
        (str(space), int(year), int(week))
        for space, year, week in training_positive_effort_contexts
    ))
    if not training_keys:
        raise ValueError("training positive-effort precipitation contexts are empty")
    missing = [key for key in training_keys if key not in weekly_mm]
    if missing:
        raise ValueError(f"missing weekly precipitation for training contexts: {missing[:10]}")

    training_values = tuple(float(weekly_mm[key]) for key in training_keys)
    mean = statistics.fmean(training_values)
    sd = statistics.pstdev(training_values)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("training weekly precipitation must have positive finite SD")
    standardized = {
        key: (float(value) - mean) / sd
        for key, value in weekly_mm.items()
    }
    return {
        "mean_mm": mean,
        "sd_mm": sd,
        "training_context_count": len(training_keys),
        "training_contexts": [list(key) for key in training_keys],
        "precip_z_train": standardized,
    }
