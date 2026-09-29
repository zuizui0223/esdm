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


def test_contract_freezes_exploratory_boundary_and_preflight_receipt():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "docs" / "replication" / "E3_MICA_EXPLORATORY_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    receipt = json.loads(
        (
            root
            / "docs"
            / "replication"
            / "E3_MICA_EXPLORATORY_PREFLIGHT_RESULT.json"
        ).read_text(encoding="utf-8")
    )

    assert contract["status"] == "PREFLIGHT_PASS_FIT_NOT_AUTHORIZED"
    relation = contract["relationship_to_prior_programmes"]
    assert relation["e2_status_remains"] == "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY"
    assert relation["reopens_e2"] is False
    assert relation["rescues_e2_claim"] is False
    assert relation["classification"] == "exploratory_real_data_analysis"

    assert receipt["status"] == "E3_PREFLIGHT_PASS"
    assert receipt["decision"]["preflight_passed"] is True
    assert receipt["decision"]["exploratory_fit_authorized_by_this_receipt"] is False
    assert receipt["qualified_geometry"]["training_deployment_count"] == 805
    assert receipt["qualified_geometry"]["heldout_deployment_count"] == 733
    assert (
        receipt["qualified_fingerprints"]["training_ids_sha256"]
        == "a1e08526edb3d1f329fc7a4e9a2efa2bc4dc50313b393026a429f3a87d57f566"
    )
    assert (
        receipt["qualified_fingerprints"]["training_role_map_sha256"]
        == "1fcd776854484ed5b0e19c20b49aed81fa22d5947b5d26120c50155e1369c7e4"
    )
    assert contract["execution"]["exploratory_fit_authorized_now"] is False


def test_reduced_endpoint_removes_direct_state_calibration_without_threshold_relaxation():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    reduced = json.loads(
        (
            root
            / "docs"
            / "replication"
            / "E3_MICA_REDUCED_ENDPOINT_CONTRACT.json"
        ).read_text(encoding="utf-8")
    )

    assert reduced["status"] == "REDUCED_FIXTURE_QUALIFIED_FIT_NOT_AUTHORIZED"
    stop = reduced["full_endpoint_stop"]
    assert stop["frozen_minimum_state_calibration_each_state"] == 10
    assert stop["observed_state_calibration"] == {
        "solitary": 824,
        "group": 6,
    }
    assert stop["observed_state_calibration"]["group"] < (
        stop["frozen_minimum_state_calibration_each_state"]
    )

    endpoint = reduced["reduced_endpoint"]
    assert endpoint["lower_state_calibration_minimum"] is False
    assert endpoint["reuse_state_calibration_rows_in_other_streams"] is False
    assert endpoint["reassign_training_roles"] is False
    assert endpoint["change_east_holdout"] is False
    assert endpoint["retained_training_streams"] == [
        "presence_opportunistic",
        "presence_calibrated",
        "annotated",
    ]

    claims = reduced["allowed_claims"]
    assert claims["exploratory_predictive_activity_gain"] is True
    assert claims["exploratory_predictive_state_gain_without_independent_calibration"] is True
    assert claims["independently_calibrated_state_effect"] is False
    assert claims["confirmatory_replication"] is False
    assert claims["e2_rescue"] is False

    execution = reduced["execution"]
    assert execution["reduced_fixture_capture_authorized_now"] is False\n    assert execution["reduced_fixture_capture_consumed"] is True
    assert execution["exploratory_model_fit_authorized_now"] is False
