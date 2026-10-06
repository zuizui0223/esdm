from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_henrich10_osf_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_HENRICH10_OSF_MANIFEST_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-henrich10-osf-manifest-once.yml"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_henrich10_manifest_contract_forbids_file_content_and_response():
    value = _contract()
    assert value["status"] == "FROZEN_MANIFEST_NOT_AUTHORIZED"
    fw = value["response_firewall"]
    assert fw["project_metadata_read_authorized"] is True
    assert fw["storage_manifest_metadata_read_authorized"] is True
    assert fw["recursive_folder_manifest_read_authorized"] is True
    assert fw["file_content_read_authorized"] is False
    assert fw["file_download_authorized"] is False
    assert fw["file_preview_authorized"] is False
    assert fw["biological_rows_read_authorized"] is False
    assert fw["focal_response_opening_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False
    assert value["decision_boundary"]["G2_pass_authorized"] is False
    assert value["decision_boundary"]["final_G4_pass_authorized"] is False


def test_henrich10_manifest_parser_uses_names_only_for_child_route_hints():
    root = "https://api.osf.io/v2/nodes/3vwkq/files/osfstorage/?page[size]=100"
    child = (
        "https://api.osf.io/v2/nodes/3vwkq/files/"
        "osfstorage/folder123/?page[size]=100"
    )
    payloads = {
        "https://api.osf.io/v2/nodes/3vwkq/": {
            "data": {"attributes": {"title": "x", "public": True}}
        },
        root: {
            "data": [
                {
                    "id": "folder123",
                    "attributes": {
                        "name": "metadata",
                        "kind": "folder",
                        "materialized_path": "/metadata/",
                        "provider": "osfstorage",
                        "size": None,
                    },
                },
                {
                    "id": "file1",
                    "attributes": {
                        "name": "deployment_effort.csv",
                        "kind": "file",
                        "materialized_path": "/deployment_effort.csv",
                        "provider": "osfstorage",
                        "size": 123,
                    },
                },
            ],
            "links": {"next": None},
        },
        child: {
            "data": [
                {
                    "id": "file2",
                    "attributes": {
                        "name": "distance_calibration.csv",
                        "kind": "file",
                        "materialized_path": "/metadata/distance_calibration.csv",
                        "provider": "osfstorage",
                        "size": 456,
                    },
                }
            ],
            "links": {"next": None},
        },
    }

    requested = []

    def fake_get(url: str) -> dict:
        requested.append(url)
        return payloads[url]

    result = build_manifest(_contract(), getter=fake_get)
    assert result["manifest"]["file_count"] == 2
    assert result["manifest"]["folder_count"] == 1
    assert result["decision"]["manifest_supports_effort_child"] is True
    assert result["decision"]["manifest_supports_calibration_child"] is True
    assert result["decision"]["child_contract_recommended"] is True
    assert result["decision"]["candidate_qualified"] is False
    assert result["response_boundary"]["file_downloads_followed"] == 0
    assert result["response_boundary"]["file_contents_opened"] == 0
    assert all("download" not in url for url in requested)


def test_henrich10_workflow_is_marker_only_and_pins_contract_blob():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/henrich10-osf-manifest-v1" in text
    assert "E5_HENRICH10_OSF_MANIFEST_AUTHORIZED.json" in text
    assert "4f4c461c413f4ee02e1dd9481ceb96d33bd28442" in text
    assert "workflow_dispatch" not in text
    assert "file_content_read_authorized" in text
    assert "api.osf.io/v2/nodes/3vwkq/" in text
    assert "osf.io/download" not in text
