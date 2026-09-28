from __future__ import annotations

import csv
import io
import zipfile

from esdm.validate.e3_mica_exploratory import (
    audit_nonpositive_deployment_durations,
    sanitize_archive_by_deployment_ids,
)


BAD_ID = "bad-zero"


def _fixture(path):
    dep = io.StringIO()
    writer = csv.DictWriter(
        dep,
        fieldnames=[
            "deploymentID",
            "deploymentStart",
            "deploymentEnd",
            "longitude",
            "latitude",
        ],
    )
    writer.writeheader()
    writer.writerows(
        [
            {
                "deploymentID": "good-west",
                "deploymentStart": "2021-01-01T00:00:00Z",
                "deploymentEnd": "2021-01-02T00:00:00Z",
                "longitude": "4.0",
                "latitude": "51.0",
            },
            {
                "deploymentID": BAD_ID,
                "deploymentStart": "2021-01-03T00:00:00Z",
                "deploymentEnd": "2021-01-03T00:00:00Z",
                "longitude": "6.084",
                "latitude": "52.939",
            },
        ]
    )

    obs = io.StringIO()
    writer = csv.DictWriter(
        obs,
        fieldnames=[
            "deploymentID",
            "eventID",
            "scientificName",
            "count",
        ],
    )
    writer.writeheader()
    writer.writerows(
        [
            {
                "deploymentID": "good-west",
                "eventID": "e1",
                "scientificName": "do-not-use-for-filter",
                "count": "999",
            },
            {
                "deploymentID": BAD_ID,
                "eventID": "e2",
                "scientificName": "different-taxon",
                "count": "1",
            },
            {
                "deploymentID": BAD_ID,
                "eventID": "e3",
                "scientificName": "another-taxon",
                "count": "50",
            },
        ]
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("mica/deployments.csv", dep.getvalue())
        z.writestr("mica/observations.csv", obs.getvalue())


def test_metadata_audit_excludes_zero_duration_without_opening_observations(tmp_path):
    source = tmp_path / "source.zip"
    _fixture(source)

    result = audit_nonpositive_deployment_durations(source)

    assert result["deployment_row_count"] == 2
    assert result["nonpositive_duration_count"] == 1
    assert result["zero_duration_count"] == 1
    assert result["negative_duration_count"] == 0
    assert result["excluded_deployment_ids"] == [BAD_ID]
    assert result["observations_data_rows_read"] == 0
    assert result["scientific_name_values_read"] is False
    assert result["count_values_read"] is False


def test_sanitizer_filters_response_rows_by_deployment_id_only(tmp_path):
    source = tmp_path / "source.zip"
    output = tmp_path / "sanitized.zip"
    _fixture(source)

    result = sanitize_archive_by_deployment_ids(
        source,
        output,
        excluded_deployment_ids={BAD_ID},
    )

    assert result["removed_deployment_rows"] == 1
    assert result["removed_observation_rows"] == 2
    assert result["retained_observation_rows"] == 1
    assert result["row_filter_uses_only_deployment_id"] is True

    with zipfile.ZipFile(output) as z:
        deployments = z.read("mica/deployments.csv").decode("utf-8")
        observations = z.read("mica/observations.csv").decode("utf-8")
    assert BAD_ID not in deployments
    assert BAD_ID not in observations
    assert "good-west" in deployments
    assert "good-west" in observations
