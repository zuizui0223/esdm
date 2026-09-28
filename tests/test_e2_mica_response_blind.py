from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import zipfile

import pytest

from esdm.validate.e2_mica_response_blind import (
    qualify_e2_mica_archive,
)


def _deployment_rows():
    rows = []
    # 80 western training candidates.
    for i in range(80):
        rows.append(
            {
                "deploymentID": f"west-{i:03d}",
                "latitude": 51.0 + 0.001 * (i % 10),
                "longitude": 4.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    # 20 eastern heldout candidates with a very large strict gap.
    for i in range(20):
        rows.append(
            {
                "deploymentID": f"east-{i:03d}",
                "latitude": 52.0 + 0.001 * (i % 10),
                "longitude": 8.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    return rows


def _zip_fixture(path: Path, *, observation_header=None):
    rows = _deployment_rows()
    deployment_buffer = io.StringIO()
    writer = csv.DictWriter(
        deployment_buffer,
        fieldnames=[
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

    if observation_header is None:
        observation_header = [
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            "count",
        ]

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mica/datapackage.json", json.dumps({"name": "mica"}))
        archive.writestr("mica/deployments.csv", deployment_buffer.getvalue())
        # The bytes after the first newline are intentionally invalid UTF-8.
        # A response-blind qualifier that reads past the header will fail.
        archive.writestr(
            "mica/observations.csv",
            (",".join(observation_header) + "\n").encode("utf-8") + b"\xff\xfe\xfa",
        )


def test_response_blind_qualifier_reads_deployments_and_observation_header_only(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive)

    result = qualify_e2_mica_archive(archive)

    assert result["status"] == "RESPONSE_BLIND_GEOMETRY_HEADER_PASS"
    assert result["geometry"]["deployment_count"] == 100
    assert result["geometry"]["training_deployment_count"] == 80
    assert result["geometry"]["heldout_deployment_count"] == 20
    assert result["geometry"]["strict_east_extrapolation"] is True
    assert result["geometry"]["longitude_gap"] > 3.0
    assert result["roles"]["all_minima_pass"] is True

    boundary = result["response_boundary"]
    assert boundary["observations_data_rows_read"] == 0
    assert boundary["scientific_name_values_read"] is False
    assert boundary["count_values_read"] is False
    assert boundary["state_values_read"] is False
    assert boundary["authorizes_temporal_opening"] is False
    assert boundary["authorizes_full_response_opening"] is False


def test_east_holdout_uses_largest_gap_and_is_strict(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive)

    result = qualify_e2_mica_archive(archive)
    geometry = result["geometry"]

    assert geometry["max_training_longitude"] < geometry["min_heldout_longitude"]
    assert geometry["max_training_longitude"] < 5.0
    assert geometry["min_heldout_longitude"] >= 8.0


def test_qualifier_rejects_missing_required_observation_header_without_reading_rows(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(
        archive,
        observation_header=[
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            # count deliberately missing
        ],
    )

    with pytest.raises(ValueError, match="observations header missing required columns"):
        qualify_e2_mica_archive(archive)


def test_role_assignment_is_deterministic_and_all_training_roles_have_minimum(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive)

    first = qualify_e2_mica_archive(archive)
    second = qualify_e2_mica_archive(archive)

    assert first["roles"]["training_counts"] == second["roles"]["training_counts"]
    assert first["fingerprints"]["training_role_map_sha256"] == (
        second["fingerprints"]["training_role_map_sha256"]
    )
    assert all(
        value >= 8
        for value in first["roles"]["training_counts"].values()
    )


def test_contracts_keep_mica_candidate_response_blind():
    root = Path(__file__).resolve().parents[1]
    parent = json.loads(
        (root / "docs" / "replication" / "E2_EMPIRICAL_REPLICATION_CONTRACT.json").read_text()
    )
    child = json.loads(
        (root / "docs" / "replication" / "E2_MICA_MUSKRAT_CANDIDATE_CONTRACT.json").read_text()
    )

    assert parent["candidate_selection"]["selected_candidate"] == "MICA_MUSKRAT"
    assert parent["current_authorization"]["candidate_selected"] is True
    assert (
        parent["current_authorization"]["response_blind_geometry_header_opening"]
        == "completed_pass"
    )
    assert (
        parent["current_authorization"]["temporal_integrity_opening"]
        == "completed_pass"
    )
    assert (
        parent["current_authorization"]["response_blind_climate"]
        == "completed_pass"
    )
    assert (
        parent["current_authorization"]["full_ecological_response_opening"]
        is False
    )
    assert parent["current_authorization"]["model_fitting"] is False

    assert child["focal_taxon"]["scientific_name"] == "Ondatra zibethicus"
    assert child["focal_taxon"]["selected_before_observation_rows"] is True
    assert child["scientific_boundary"]["observation_rows_opened"] == 0
    assert child["scientific_boundary"]["temporal_opening_authorized_by_this_contract"] is False
    assert child["scientific_boundary"]["full_response_opening_authorized_by_this_contract"] is False
