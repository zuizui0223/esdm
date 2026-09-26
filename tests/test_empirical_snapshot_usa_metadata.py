from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from esdm.validate.empirical_snapshot_usa import (
    _site_rank,
    _stream_bucket,
    parse_deployment_metadata,
    parse_sequence_header,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_USA_2024_HEADER_CONTRACT.json"
REGISTRY = ROOT / "docs" / "empirical" / "EMPIRICAL_R5B_CANDIDATE_REGISTRY_V1.json"


def _deployment_id_for_bucket(target: int, offset: int) -> str:
    index = offset
    while True:
        value = f"dep-{target}-{index:05d}"
        bucket = _stream_bucket(value)
        if (
            target == 0 and bucket <= 63
            or target == 1 and 64 <= bucket <= 127
            or target == 2 and 128 <= bucket <= 207
            or target == 3 and 208 <= bucket <= 255
        ):
            return value
        index += 1


def _deployment_csv() -> bytes:
    fieldnames = [
        "Project",
        "State",
        "Camera_Trap_Array",
        "Site_Name",
        "Deployment_ID",
        "Start_Date",
        "End_Date",
        "Survey_Nights",
        "Latitude",
        "Longitude",
    ]
    rows = []
    for index in range(64):
        target = index % 4
        rows.append(
            {
                "Project": "fixture",
                "State": "XX",
                "Camera_Trap_Array": f"array-{index // 8:02d}",
                "Site_Name": f"site-{index:03d}",
                "Deployment_ID": _deployment_id_for_bucket(target, index * 100),
                "Start_Date": "2024-09-01",
                "End_Date": "2024-10-31",
                "Survey_Nights": "61",
                "Latitude": str(30.0 + 0.05 * index),
                "Longitude": str(-104.0 + 0.25 * index),
            }
        )
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _sequence_header() -> bytes:
    return (
        "Project,Camera_Trap_Array,Deployment_ID,Sequence_ID,Start_Time,End_Time,"
        "Class,Order,Family,Genus,Species,Common_Name,Age,Sex,Group_Size,"
        "Individual_Animal_Notes,Behavior"
    ).encode("utf-8")


def test_candidate_registry_advances_only_snapshot_usa():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert registry["status"] == "FROZEN_PRE_RESPONSE"
    assert registry["selected_candidate"] == "SNAPSHOT_USA_2024_WHITE_TAILED_DEER"

    candidates = {row["candidate_id"]: row for row in registry["candidates"]}
    assert candidates["ALGAR_BEHAVIORAL_BYCATCH"]["eligible"] is False
    assert candidates["CHICAGO_COYOTE_MANGE"]["metadata_findings"]["hour_available"] is False
    assert candidates["SMALL_MAMMAL_BOLDNESS"]["metadata_findings"]["coordinates_available"] is False
    assert candidates["SNAPSHOT_USA_2024_WHITE_TAILED_DEER"]["eligible"] is True
    assert candidates["SNAPSHOT_USA_2024_WHITE_TAILED_DEER"]["response_rows_opened"] == 0


def test_snapshot_contract_freezes_state_and_stream_rules_before_response():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["status"] == "FROZEN_PRE_RESPONSE_HEADER"
    assert contract["focal_taxon"]["genus"] == "Odocoileus"
    assert contract["focal_taxon"]["species"] == "virginianus"
    assert contract["state_contract"]["states"] == ["solitary", "group"]
    assert contract["state_contract"]["mapping"] == {
        "solitary": "integer Group_Size == 1",
        "group": "integer Group_Size >= 2",
    }
    assert contract["training_stream_partition"]["partitions_disjoint"] is True
    assert contract["training_stream_partition"]["state_calibration_exposure_in_holdout"] == 0
    assert contract["spatial_contract"]["selected_unique_sites"] == 64


def test_deployment_metadata_freezes_64_sites_strict_east_holdout_and_four_streams():
    result = parse_deployment_metadata(_deployment_csv())

    assert result["selected_site_count"] == 64
    assert len(result["selected_sites"]) == 64
    assert [row["spatial_unit"] for row in result["selected_sites"]] == sorted(
        result["selected_spatial_units"]
    )
    assert {row["partition"] for row in result["selected_sites"]} == {
        "training",
        "heldout",
    }
    assert all(
        isinstance(row["latitude"], float) and isinstance(row["longitude"], float)
        for row in result["selected_sites"]
    )
    assert result["training_site_count"] > 0
    assert result["heldout_site_count"] >= 13
    assert result["training_longitude_max"] < result["heldout_longitude_min"]
    assert set(result["training_spatial_units"]).isdisjoint(result["heldout_spatial_units"])
    assert all(
        count > 0
        for count in result["training_stream_deployment_counts"].values()
    )
    assert result["state_calibration_heldout_exposure"] == 0


def test_site_selection_is_hash_deterministic_not_longitude_selected():
    result = parse_deployment_metadata(_deployment_csv())

    expected = sorted(
        result["selected_spatial_units"],
        key=lambda spatial_unit: (_site_rank(spatial_unit), spatial_unit),
    )
    assert set(expected) == set(result["selected_spatial_units"])


def test_sequence_header_is_validated_without_response_row_access():
    result = parse_sequence_header(_sequence_header())

    assert result["required_columns_present"] is True
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert "Group_Size" in result["columns"]
    assert "Start_Time" in result["columns"]


def test_sequence_header_fails_closed_when_group_size_missing():
    header = _sequence_header().decode("utf-8").replace(",Group_Size", "")

    with pytest.raises(ValueError, match="missing required columns"):
        parse_sequence_header(header.encode("utf-8"))


def test_deployment_metadata_rejects_non_strict_or_invalid_effort():
    text = _deployment_csv().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    rows[0]["Survey_Nights"] = "1000"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

    with pytest.raises(ValueError, match="active fraction outside"):
        parse_deployment_metadata(out.getvalue().encode("utf-8"))
