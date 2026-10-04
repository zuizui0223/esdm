from __future__ import annotations

import json
from pathlib import Path

from scripts.precheck_e5_kays41_dictionary import _concepts, _plain_rtf, precheck


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication" / "E5_KAYS41_DICTIONARY_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e5-kays41-dictionary-once.yml"
)


def test_dictionary_contract_forbids_all_response_files():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert value["status"] == "FROZEN_PRECHECK_NOT_AUTHORIZED"
    fw = value["response_firewall"]
    assert fw["data_dictionary_full_text_read_authorized"] is True
    assert fw["any_response_file_download_authorized"] is False
    assert fw["spatial_raw_detections_open_authorized"] is False
    assert fw["temporal_detection_rate_open_authorized"] is False
    assert fw["focal_species_values_authorized"] is False
    assert fw["detection_rows_authorized"] is False
    assert value["decision_boundary"]["candidate_qualification_authorized"] is False


def test_rtf_parser_detects_only_schema_concepts(tmp_path):
    rtf = (
        r"{\rtf1\ansi "
        "Deployment_ID deployment_start deployment_end Study_Area Site_ID "
        "camera_model Camera_ID photo_date photo_time occasion latitude longitude}"
    ).encode("latin-1")
    path = tmp_path / "dictionary.rtf"
    path.write_bytes(rtf)

    value = precheck(path, CONTRACT)
    concepts = value["schema_concepts"]
    assert all(concepts.values())
    b = value["response_boundary"]
    assert b["dictionary_files_read"] == 1
    assert b["response_files_downloaded"] == 0
    assert b["response_files_opened"] == 0
    assert b["detection_rows_read"] == 0
    assert b["species_values_read"] == 0
    assert b["focal_response_opened"] is False
    assert value["decision"]["candidate_qualified"] is False


def test_plain_rtf_rejects_non_rtf():
    try:
        _plain_rtf(b"not an rtf")
    except ValueError as exc:
        assert "not RTF" in str(exc)
    else:
        raise AssertionError("non-RTF input must fail closed")


def test_dictionary_workflow_is_marker_only_and_never_names_response_downloads():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/kays41-dictionary-v1" in text
    assert "E5_KAYS41_DICTIONARY_AUTHORIZED.json" in text
    assert "454eb1ec3ab76f55dfb258cbdf1b4d081b2c0c06" in text
    assert "api/v2/files/235085/download" in text
    assert "workflow_dispatch" not in text
    assert "response_file_download_authorized" in text
    assert "Spatial_Raw_detections.csv" not in text
    assert "Temporal_Detection_rate.csv" not in text
    assert "seasonal.zip" not in text
    assert "Temporal_Species_diversity_accumulation.zip" not in text
    assert "same_authorization_rerun_allowed" in text
