from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path

import pytest

from esdm.validate.empirical_snapshot_usa_daymet import (
    build_cache_manifest,
    build_precipitation_covariate_table,
    cache_manifest_entry,
    daymet_site_request,
    deployment_week_contexts,
    iso_week_precipitation,
    parse_daymet_prcp_response,
    standardize_weekly_precipitation,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "docs"
    / "empirical"
    / "SNAPSHOT_USA_2024_DAYMET_PRECIPITATION_CONTRACT.json"
)


def _daymet_csv(scale: float = 1.0) -> bytes:
    lines = [
        "Latitude: 43.10000000",
        "Longitude: -85.30000000",
        "Daymet Software Version: 4.1",
        "year,yday,prcp (mm/day)",
    ]
    for yday in range(1, 366):
        value = scale * ((yday % 11) + 1) / 10.0
        lines.append(f"2024,{yday},{value:.6f}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def test_daymet_contract_pins_public_product_before_response():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["status"] == "FROZEN_PRE_RESPONSE_CLIMATE"
    assert contract["product"]["version"] == "4.1"
    assert contract["product"]["dataset_doi"] == "10.3334/ORNLDAAC/2129"
    assert contract["product"]["earthdata_concept_id"] == "C2532426483-ORNL_CLOUD"
    assert contract["product"]["variable"] == "prcp"
    assert contract["product"]["year"] == 2024
    assert contract["product"]["single_pixel_tool"]["tool_doi"] == (
        "10.3334/ORNLDAAC/2361"
    )
    assert contract["scientific_boundary"]["response_data_rows_allowed_during_this_stage"] == 0
    assert contract["scientific_boundary"]["model_fits_allowed_during_this_stage"] == 0


def test_daymet_request_is_canonical_and_domain_checked():
    request = daymet_site_request("array|site", 43.1, -85.3)

    assert request.url == (
        "https://daymet.ornl.gov/single-pixel/api/data?"
        "lat=43.10000000&lon=-85.30000000&vars=prcp&years=2024"
    )
    assert request.cache_filename.endswith(".csv")
    assert len(request.cache_filename) == 24

    with pytest.raises(ValueError, match="latitude"):
        daymet_site_request("bad-lat", 59.0, -85.0)
    with pytest.raises(ValueError, match="longitude"):
        daymet_site_request("bad-lon", 40.0, -140.0)


def test_daymet_response_requires_exact_365_days_and_nonnegative_precipitation():
    parsed = parse_daymet_prcp_response(_daymet_csv())

    assert len(parsed) == 365
    assert min(parsed) == date(2024, 1, 1)
    assert max(parsed) == date(2024, 12, 30)
    assert all(value >= 0.0 for value in parsed.values())

    missing = _daymet_csv().decode("utf-8").replace(
        "2024,200,0.300000\n", ""
    )
    with pytest.raises(ValueError, match="exact yday 1..365"):
        parse_daymet_prcp_response(missing.encode("utf-8"))

    negative = _daymet_csv().decode("utf-8").replace(
        "2024,100,0.200000", "2024,100,-0.200000"
    )
    with pytest.raises(ValueError, match="negative Daymet precipitation"):
        parse_daymet_prcp_response(negative.encode("utf-8"))


def test_cache_manifest_hashes_raw_bytes_and_requires_all_64_selected_sites():
    requests = [
        daymet_site_request(f"array|site-{index:02d}", 35.0 + 0.01 * index, -90.0)
        for index in range(64)
    ]
    raw = {
        request.spatial_unit: _daymet_csv(1.0 + index / 100.0)
        for index, request in enumerate(requests)
    }

    manifest = build_cache_manifest(requests, raw)

    assert manifest["selected_site_count"] == 64
    assert manifest["response_rows_opened"] == 0
    assert manifest["response_values_opened"] is False
    assert manifest["model_fits"] == 0
    assert manifest["heldout_scores"] == 0
    assert len(manifest["manifest_sha256"]) == 64
    assert [row["spatial_unit"] for row in manifest["entries"]] == sorted(raw)

    one = cache_manifest_entry(requests[0], raw[requests[0].spatial_unit])
    assert len(one["raw_sha256"]) == 64
    assert one["daily_row_count"] == 365

    with pytest.raises(ValueError, match="cache coverage mismatch"):
        build_cache_manifest(requests, dict(list(raw.items())[:-1]))


def test_iso_week_precipitation_sums_full_monday_sunday_week():
    daily = parse_daymet_prcp_response(_daymet_csv())
    context = ("array|site", 2024, 36)
    weekly = iso_week_precipitation(
        {"array|site": daily},
        [context, context],
    )

    monday = date.fromisocalendar(2024, 36, 1)
    expected = sum(daily[monday + timedelta(days=offset)] for offset in range(7))
    assert weekly == {context: pytest.approx(expected)}


def test_weekly_precipitation_fails_closed_if_any_week_day_is_absent():
    daily = parse_daymet_prcp_response(_daymet_csv())
    missing_date = date.fromisocalendar(2024, 36, 4)
    daily.pop(missing_date)

    with pytest.raises(ValueError, match="missing dates"):
        iso_week_precipitation(
            {"array|site": daily},
            [("array|site", 2024, 36)],
        )


def test_precipitation_standardization_uses_training_contexts_only():
    weekly = {
        ("train-a", 2024, 36): 10.0,
        ("train-b", 2024, 36): 20.0,
        ("heldout", 2024, 36): 1000.0,
    }
    result = standardize_weekly_precipitation(
        weekly,
        [
            ("train-a", 2024, 36),
            ("train-b", 2024, 36),
        ],
    )

    assert result["mean_mm"] == pytest.approx(15.0)
    assert result["sd_mm"] == pytest.approx(5.0)
    assert result["training_context_count"] == 2
    assert result["precip_z_train"][("train-a", 2024, 36)] == pytest.approx(-1.0)
    assert result["precip_z_train"][("train-b", 2024, 36)] == pytest.approx(1.0)
    assert result["precip_z_train"][("heldout", 2024, 36)] == pytest.approx(197.0)


def test_snapshot_survey_window_avoids_daymet_leap_year_dec31_gap():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    start, end = (
        date.fromisoformat(value)
        for value in contract["temporal_transformation"]["survey_required_date_window"]
    )

    assert start == date(2024, 8, 1)
    assert end == date(2024, 12, 19)
    assert end < date(2024, 12, 31)


def test_deployment_metadata_expands_to_unique_site_week_contexts():
    rows = [
        {
            "spatial_unit": "train-a",
            "partition": "training",
            "start_date": "2024-08-01",
            "end_date": "2024-08-10",
        },
        {
            "spatial_unit": "heldout-a",
            "partition": "heldout",
            "start_date": "2024-12-16",
            "end_date": "2024-12-19",
        },
    ]
    contexts = deployment_week_contexts(rows)

    assert contexts["training"] == (
        ("train-a", 2024, 31),
        ("train-a", 2024, 32),
    )
    assert contexts["all"] == (
        ("heldout-a", 2024, 51),
        ("train-a", 2024, 31),
        ("train-a", 2024, 32),
    )


def test_full_precipitation_table_is_pre_response_and_training_scaled():
    sites = []
    deployments = []
    raw = {}
    for index in range(64):
        spatial_unit = f"array|site-{index:02d}"
        partition = "training" if index < 48 else "heldout"
        latitude = 35.0 + 0.01 * index
        longitude = -90.0
        sites.append(
            {
                "spatial_unit": spatial_unit,
                "latitude": latitude,
                "longitude": longitude,
                "partition": partition,
            }
        )
        deployments.append(
            {
                "deployment_id": f"dep-{index:02d}",
                "spatial_unit": spatial_unit,
                "partition": partition,
                "training_stream": (
                    "state_annotated" if partition == "training" else None
                ),
                "start_date": "2024-08-01",
                "end_date": "2024-08-10",
                "survey_nights": 10,
                "inclusive_nights": 10,
                "active_fraction": 1.0,
            }
        )
        request = daymet_site_request(spatial_unit, latitude, longitude)
        raw[spatial_unit] = _daymet_csv(1.0 + index / 100.0)

    result = build_precipitation_covariate_table(
        selected_sites=sites,
        selected_deployments=deployments,
        raw_by_spatial_unit=raw,
    )

    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["context_count"] == 64 * 2
    assert result["training_context_count"] == 48 * 2
    assert result["heldout_context_count"] == 16 * 2
    assert result["training_scaler"]["sd_mm"] > 0
    assert len(result["table_sha256"]) == 64
    assert len(result["cache_manifest_sha256"]) == 64

    training = [row for row in result["rows"] if row["partition"] == "training"]
    heldout = [row for row in result["rows"] if row["partition"] == "heldout"]
    assert training and heldout
    assert abs(sum(row["precip_z_train"] for row in training) / len(training)) < 1e-12


def test_full_iso_week_window_is_frozen_beyond_response_timestamp_window():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["temporal_transformation"]["survey_required_date_window"] == [
        "2024-08-01",
        "2024-12-19",
    ]
    assert contract["temporal_transformation"][
        "daymet_required_date_window_for_full_iso_weeks"
    ] == ["2024-07-29", "2024-12-22"]
