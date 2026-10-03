from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_qld_ala_metadata import summarize


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_QLD_ALA_METADATA_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-qld-ala-metadata-once.yml"
)


def test_contract_forbids_following_data_links_and_response_opening():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fw = value["response_firewall"]
    assert fw["ala_metadata_endpoint_read_authorized"] is True
    assert fw["raw_metadata_json_artifact_authorized"] is False
    assert fw["dataset_archive_download_authorized"] is False
    assert fw["deployment_rows_read_authorized"] is False
    assert fw["observation_rows_read_authorized"] is False
    assert fw["species_fields_read_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_metadata_precheck_extracts_safe_urls_but_never_follows_them(tmp_path):
    raw = tmp_path / "metadata.json"
    raw.write_text(json.dumps({
        "uid": "dr31594",
        "name": "Camera trap surveys in Queensland's Wet Tropics 2022-2023",
        "websiteUrl": "https://example.org/resource",
        "connectionParameters": {
            "url": "https://example.org/archive.zip",
            "protocol": "DwC-A",
            "secretToken": "must-not-be-reported",
        },
        "dataLinks": [
            {"name": "archive", "type": "data", "url": "https://example.org/archive.zip"}
        ],
        "externalIdentifiers": [
            {"provider": "GBIF", "identifier": "10.15468/kjqw3f"}
        ],
    }), encoding="utf-8")

    result = summarize(raw, CONTRACT)
    assert result["safe_metadata"]["uid"] == "dr31594"
    assert result["connection_parameters"]["present"] is True
    assert result["connection_parameters"]["keys_only"] == [
        "protocol", "secretToken", "url"
    ]
    assert any(
        x["url"] == "https://example.org/archive.zip"
        for x in result["url_like_values"]
    )
    dumped = json.dumps(result)
    assert "must-not-be-reported" not in dumped
    b = result["response_boundary"]
    assert b["discovered_urls_followed"] == 0
    assert b["dataset_archive_downloaded"] is False
    assert b["deployment_rows_read"] == 0
    assert b["observation_rows_read"] == 0


def test_workflow_is_pure_marker_and_metadata_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/qld-ala-metadata-v1" in text
    assert "E5_QLD_ALA_METADATA_AUTHORIZED.json" in text
    assert "a8e2be58eb38dcacb5f857a7e328b8f59f7afefa" in text
    assert "api.ala.org.au/metadata/ws/dataResource/dr31594" in text
    assert "workflow_dispatch" not in text
    assert "follow_discovered_urls_authorized" in text
    assert "precheck_e5_qld_ala_metadata.py" in text
