from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.screen_e5_wildlife_insights_metadata import screen


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication"
    / "E5_WILDLIFE_INSIGHTS_METADATA_SCREENER_CONTRACT.json"
)


def _write_csv(path: Path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _package(tmp_path: Path, *, months=6, locations=31):
    _write_csv(
        tmp_path / "projects.csv",
        [
            "project_id",
            "project_sensor_cluster",
            "project_sensor_method",
            "project_stratification",
            "focal_country",
        ],
        [
            {
                "project_id": "p1",
                "project_sensor_cluster": "paired",
                "project_sensor_method": "motion",
                "project_stratification": "east;west",
                "focal_country": "Exampleland",
            }
        ],
    )
    _write_csv(
        tmp_path / "cameras.csv",
        ["camera_id"],
        [{"camera_id": f"c{i:03d}"} for i in range(locations)],
    )
    rows = []
    for i in range(locations):
        month = 1 + (i % months)
        rows.append(
            {
                "project_id": "p1",
                "deployment_id": f"d{i:03d}",
                "location_name": f"loc{i:03d}",
                "start_date": f"2026-{month:02d}-01",
                "end_date": f"2026-{month:02d}-28",
                "latitude": str(10.0 + i / 1000),
                "longitude": str(20.0 + i / 1000),
                "subproject_name": "east" if i % 2 else "west",
            }
        )
    _write_csv(
        tmp_path / "deployments.csv",
        [
            "project_id",
            "deployment_id",
            "location_name",
            "start_date",
            "end_date",
            "latitude",
            "longitude",
            "subproject_name",
        ],
        rows,
    )
    # If the screener accidentally opens this response-bearing file, decoding must fail.
    (tmp_path / "images.csv").write_bytes(b"\xff\xfe\x00species-response")
    return tmp_path


def test_metadata_screener_contract_forbids_response_and_final_qualification():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert value["status"] == "RESPONSE_BLIND_DISCOVERY_TOOL"
    assert value["response_policy"]["response_rows_read_must_equal"] == 0
    assert value["response_policy"]["species_or_taxon_fields_may_not_be_used"] is True
    assert "G3_CROSSED_DOMAIN" in value["automated_scope"]["may_not_qualify"]
    assert "G4_DETECTION_IDENTIFIABILITY" in value["automated_scope"]["may_not_qualify"]
    assert value["discovery_hints"]["qualification_authorized"] is False
    assert value["discovery_hints"]["focal_response_opening_authorized"] is False


def test_screener_reads_metadata_only_even_if_response_file_is_present(tmp_path):
    result = screen(_package(tmp_path))

    boundary = result["response_boundary"]
    assert boundary["response_files_opened"] is False
    assert boundary["response_rows_read"] == 0
    assert boundary["response_files_present_but_unread"] == ["images.csv"]
    assert set(boundary["allowed_files_read"]) == {
        "projects.csv",
        "cameras.csv",
        "deployments.csv",
    }


def test_screener_reports_geometry_and_temporal_hints_without_promoting_g3_g4(tmp_path):
    result = screen(_package(tmp_path, months=6, locations=31))

    assert result["schema"]["missing_required_metadata_columns"] == []
    assert result["schema"]["geography_coordinates_present"] is True
    assert result["preliminary_gate_hints"]["G2_SCHEMA_EFFORT_TIME"] == "PASS_METADATA_ONLY"
    assert result["preliminary_gate_hints"]["G5_PHYSICAL_REPLICATION"] == "POTENTIAL"
    assert result["preliminary_gate_hints"]["G6_TEMPORAL_SUPPORT"] == "POTENTIAL"
    assert result["preliminary_gate_hints"]["G3_CROSSED_DOMAIN"] == (
        "MANUAL_CROSSED_DOMAIN_REVIEW_REQUIRED"
    )
    assert result["preliminary_gate_hints"]["G4_DETECTION_IDENTIFIABILITY"] == (
        "MANUAL_CALIBRATION_REVIEW_REQUIRED"
    )
    assert result["projects"][0]["unique_physical_locations"] == 31
    assert result["projects"][0]["distinct_calendar_months_with_exposure"] == 6


def test_screener_does_not_relax_frozen_six_month_hint(tmp_path):
    result = screen(_package(tmp_path, months=5, locations=31))

    assert result["projects"][0]["distinct_calendar_months_with_exposure"] == 5
    assert result["projects"][0]["six_month_temporal_hint"] is False
    assert result["preliminary_gate_hints"]["G6_TEMPORAL_SUPPORT"] == (
        "NO_PROJECT_WITH_6_MONTHS"
    )


def test_screener_fails_g2_hint_on_duplicate_deployment_identity(tmp_path):
    package = _package(tmp_path)
    deployments = list(csv.DictReader((package / "deployments.csv").open()))
    deployments[1]["deployment_id"] = deployments[0]["deployment_id"]
    _write_csv(
        package / "deployments.csv",
        list(deployments[0]),
        deployments,
    )

    result = screen(package)
    assert result["schema"]["duplicate_deployment_ids"] == ["d000"]
    assert result["preliminary_gate_hints"]["G2_SCHEMA_EFFORT_TIME"] == (
        "FAIL_OR_INCOMPLETE_METADATA"
    )
