from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import zipfile

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive
from esdm.validate.e2_mica_temporal_integrity import (
    audit_e2_mica_temporal_integrity,
)


def _deployment_rows():
    rows = []
    for i in range(80):
        rows.append(
            {
                "deploymentID": f"west-{i:03d}",
                "latitude": 51.0,
                "longitude": 4.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    for i in range(20):
        rows.append(
            {
                "deploymentID": f"east-{i:03d}",
                "latitude": 52.0,
                "longitude": 8.0 + 0.0001 * i,
                "deploymentStart": "2025-01-01T00:00:00+00:00",
                "deploymentEnd": "2025-01-31T23:59:59+00:00",
            }
        )
    return rows


def _observations(*, late_events=1, late_seconds=3600, before_start=False, forbidden_token="secret"):
    rows = []
    for i in range(200):
        event_start = "2025-01-15T12:00:00+00:00"
        if i < late_events:
            # Deployment ends at 23:59:59 on Jan 31.
            if late_seconds == 3600:
                event_start = "2025-02-01T00:59:59+00:00"
            else:
                event_start = "2025-02-02T00:00:00+00:00"
        if before_start and i == 0:
            event_start = "2024-12-31T23:00:00+00:00"
        rows.append(
            {
                "observationID": f"obs-{i:04d}",
                "deploymentID": "west-000",
                "eventID": f"event-{i:04d}",
                "eventStart": event_start,
                "observationLevel": "event",
                "observationType": "animal",
                "scientificName": f"{forbidden_token}-{i % 3}",
                "count": str(1 + (i % 5)),
            }
        )
    return rows


def _zip_fixture(path: Path, *, late_events=1, late_seconds=3600, before_start=False, forbidden_token="secret"):
    deployments = io.StringIO()
    writer = csv.DictWriter(
        deployments,
        fieldnames=[
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ],
    )
    writer.writeheader()
    writer.writerows(_deployment_rows())

    observations = io.StringIO()
    writer = csv.DictWriter(
        observations,
        fieldnames=[
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            "count",
        ],
    )
    writer.writeheader()
    writer.writerows(
        _observations(
            late_events=late_events,
            late_seconds=late_seconds,
            before_start=before_start,
            forbidden_token=forbidden_token,
        )
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mica/datapackage.json", json.dumps({"name": "mica"}))
        archive.writestr("mica/deployments.csv", deployments.getvalue())
        archive.writestr("mica/observations.csv", observations.getvalue())


def _receipt(path: Path):
    result = qualify_e2_mica_archive(path)
    return {
        "result": {
            "status": result["status"],
            "candidate_id": result["candidate_id"],
            "archive_sha256": result["archive"]["sha256"],
            "deployments_sha256": result["archive"]["deployments_sha256"],
            "deployment_count": result["geometry"]["deployment_count"],
            "training_deployment_count": result["geometry"]["training_deployment_count"],
            "heldout_deployment_count": result["geometry"]["heldout_deployment_count"],
            "max_training_longitude": result["geometry"]["max_training_longitude"],
            "min_heldout_longitude": result["geometry"]["min_heldout_longitude"],
            "longitude_gap": result["geometry"]["longitude_gap"],
            "training_role_counts": result["roles"]["training_counts"],
            "fingerprints": result["fingerprints"],
        }
    }


def test_temporal_pass_quarantines_one_of_two_hundred_events(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive, late_events=1, late_seconds=3600)

    result = audit_e2_mica_temporal_integrity(archive, _receipt(archive))

    assert result["status"] == "TEMPORAL_INTEGRITY_PASS"
    assert result["events"]["unique_animal_event_count"] == 200
    assert result["events"]["before_start_count"] == 0
    assert result["events"]["after_end_count"] == 1
    assert result["events"]["after_end_over_24h_count"] == 0
    assert result["quarantine"]["event_count"] == 1
    assert result["quarantine"]["fraction_of_unique_animal_events"] == 0.005
    assert len(result["quarantine"]["event_identity_set_sha256"]) == 64
    assert result["decision"]["passed"] is True
    assert result["decision"]["authorizes_full_response"] is False


def test_temporal_stop_if_after_end_exceeds_24_hours(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive, late_events=1, late_seconds=90000)

    result = audit_e2_mica_temporal_integrity(archive, _receipt(archive))

    assert result["status"] == "STOP_TEMPORAL_INTEGRITY"
    assert result["events"]["after_end_over_24h_count"] == 1
    assert "after_end_over_24_hours" in result["decision"]["stop_reasons"]


def test_temporal_stop_if_before_start_event_exists(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive, late_events=0, before_start=True)

    result = audit_e2_mica_temporal_integrity(archive, _receipt(archive))

    assert result["status"] == "STOP_TEMPORAL_INTEGRITY"
    assert result["events"]["before_start_count"] == 1
    assert "before_deployment_start" in result["decision"]["stop_reasons"]


def test_temporal_stop_if_quarantine_fraction_exceeds_half_percent(tmp_path: Path):
    archive = tmp_path / "mica.zip"
    _zip_fixture(archive, late_events=2, late_seconds=3600)

    result = audit_e2_mica_temporal_integrity(archive, _receipt(archive))

    assert result["status"] == "STOP_TEMPORAL_INTEGRITY"
    assert result["quarantine"]["event_count"] == 2
    assert result["quarantine"]["fraction_of_unique_animal_events"] == 0.01
    assert "quarantine_fraction_above_0_005" in result["decision"]["stop_reasons"]


def test_temporal_result_is_invariant_to_forbidden_scientific_name_and_count_values(tmp_path: Path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _zip_fixture(first, forbidden_token="taxon-A")
    _zip_fixture(second, forbidden_token="taxon-B")

    a = audit_e2_mica_temporal_integrity(first, _receipt(first))
    b = audit_e2_mica_temporal_integrity(second, _receipt(second))

    assert a["events"] == b["events"]
    assert a["quarantine"]["event_count"] == b["quarantine"]["event_count"]
    assert (
        a["quarantine"]["fraction_of_unique_animal_events"]
        == b["quarantine"]["fraction_of_unique_animal_events"]
    )
    assert a["scan"]["scientific_name_values_read"] is False
    assert a["scan"]["count_values_read"] is False
    assert a["scan"]["focal_taxon_filtering_performed"] is False
    assert a["scan"]["state_mapping_performed"] is False


def test_temporal_contract_allows_only_five_observation_columns():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (
            root
            / "docs"
            / "replication"
            / "E2_MICA_TEMPORAL_INTEGRITY_CONTRACT.json"
        ).read_text()
    )

    assert contract["allowed_observation_columns"] == [
        "deploymentID",
        "eventID",
        "eventStart",
        "observationLevel",
        "observationType",
    ]
    assert "scientificName" in contract["forbidden_observation_value_access"]
    assert "count" in contract["forbidden_observation_value_access"]
    assert contract["response_boundary"]["full_response_opening_allowed"] is False
    assert contract["next_stage"]["separate_authorization_required"] is True
