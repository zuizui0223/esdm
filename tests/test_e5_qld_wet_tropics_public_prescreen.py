from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.precheck_e5_qld_wet_tropics_deployments import (
    fetch_collection,
    summarize_deployments,
)


ROOT = Path(__file__).resolve().parents[1]
SCREEN = (
    ROOT / "docs" / "replication"
    / "E5_CANDIDATE_QLD_WET_TROPICS_PUBLIC_PRESCREEN.json"
)
CONTRACT = (
    ROOT / "docs" / "replication"
    / "E5_QLD_WET_TROPICS_DEPLOYMENT_METADATA_CONTRACT.json"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_wet_tropics_public_prescreen_keeps_response_closed():
    value = _read(SCREEN)
    assert value["status"] == "E5_CANDIDATE_NOT_YET_QUALIFIED"
    boundary = value["response_boundary"]
    assert boundary["deployment_rows_read"] == 0
    assert boundary["observation_rows_read"] == 0
    assert boundary["focal_response_opened"] is False
    assert value["gates"]["G1_INDEPENDENT_SOURCE"] == "PASS"
    assert value["decision"]["candidate_qualified"] is False
    assert value["decision"]["observation_resource_opening_authorized"] is False


def test_wet_tropics_acquisition_contract_forbids_observations_and_media():
    value = _read(CONTRACT)
    assert value["status"] == "FROZEN_METADATA_ACQUISITION_NOT_AUTHORIZED"
    assert value["allowed_collections"] == ["metadata", "deployments"]
    assert value["forbidden_collections"] == ["observations", "media"]
    firewall = value["response_firewall"]
    assert firewall["observation_collection_query_authorized"] is False
    assert firewall["media_collection_query_authorized"] is False
    assert firewall["species_fields_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_deployment_summarizer_uses_only_response_independent_geometry():
    rows = [
        {
            "deploymentID": "d1",
            "locationID": "loc1",
            "locationName": "A_bush",
            "latitude": -17.0,
            "longitude": 145.0,
            "deploymentStart": "2022-09-20T00:00:00+10:00",
            "deploymentEnd": "2023-01-10T00:00:00+10:00",
            "cameraID": "cam1",
            "cameraModel": "Reconyx",
            "featureType": "bush",
            "projectName": "ZAmir_QLD_Wet_Tropics_2022_WildObsID_0001",
        },
        {
            "deploymentID": "d2",
            "locationID": "loc2",
            "locationName": "B_road",
            "latitude": -16.5,
            "longitude": 145.4,
            "deploymentStart": "2022-11-01T00:00:00+10:00",
            "deploymentEnd": "2023-03-19T00:00:00+10:00",
            "cameraID": "cam2",
            "cameraModel": "Bushnell",
            "featureType": "road",
            "projectName": "ZAmir_QLD_Wet_Tropics_2022_WildObsID_0001",
        },
    ]
    value = summarize_deployments(rows)
    boundary = value["response_boundary"]
    assert boundary["collections_queried"] == ["deployments"]
    assert boundary["observation_collection_queried"] is False
    assert boundary["observation_rows_read"] == 0
    assert value["deployment_geometry"]["row_count"] == 2
    assert value["deployment_geometry"]["unique_physical_location_candidates"] == 2
    assert value["deployment_geometry"]["distinct_calendar_month_count"] == 7
    assert value["protocol_metadata"]["feature_type_counts"] == {
        "bush": 1, "road": 1
    }


def test_deployment_summarizer_fails_closed_if_response_keys_leak():
    with pytest.raises(ValueError, match="response-bearing keys"):
        summarize_deployments([
            {
                "deploymentID": "d1",
                "locationID": "loc1",
                "deploymentStart": "2022-09-01T00:00:00+10:00",
                "deploymentEnd": "2022-10-01T00:00:00+10:00",
                "scientificName": "must-not-appear",
            }
        ])


def test_api_helper_refuses_observation_collection_before_network_call():
    with pytest.raises(ValueError, match="not response-blind-authorized"):
        fetch_collection("dummy-secret", "observations", "project")
