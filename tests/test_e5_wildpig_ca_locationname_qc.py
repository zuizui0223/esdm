from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import pytest

from scripts.audit_e5_wildpig_ca_locationname import (
    git_blob_sha,
    run_audit,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E5_WILDPIG_CA_LOCATIONNAME_QC_CONTRACT.json"
WORKFLOW = ROOT / ".github" / "workflows" / "e5-wildpig-ca-locationname-qc-once.yml"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _fixture(summer_labels):
    contract = copy.deepcopy(_contract())
    contents = {}
    for spec in contract["inputs"]:
        season = spec["season"]
        labels = summer_labels if season == "summer" else [
            f"site_{n:03d}" for n in range(1, 49)
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["LocationName", "ImageDate", "timeRad", "Species"])
        for idx, label in enumerate(labels):
            writer.writerow([label, "06/01/2016", "0.5", "wild pig"])
        payload = output.getvalue().encode("utf-8")
        spec["size_bytes"] = len(payload)
        spec["git_blob_sha"] = git_blob_sha(payload)
        contents[spec["path"]] = payload

    def fake_fetch(spec, commit):
        assert commit == "bc97ff80ec91aba03f58f06629c7e8dfff9eb85d"
        return contents[spec["path"]]

    return contract, fake_fetch


def test_qc_detects_434_labels_and_shared_48_without_reading_other_values():
    labels = [f"site_{i:03d}" for i in range(1, 435)]
    contract, fake_fetch = _fixture(labels)
    result = run_audit(contract, fake_fetch)
    assert result["status"] == "PERSISTENT_RAW_LABEL_GRANULARITY_CONFLICT"
    summer = result["seasonal_identifier_summaries"]["summer"]
    assert summer["raw_unique_locationname_labels"] == 434
    assert summer["normalized_unique_locationname_labels"] == 434
    assert summer["raw_labels_shared_with_any_other_season"] == 48
    assert summer["raw_labels_unique_to_this_season"] == 386
    assert result["decision"]["original_statistical_label_unchanged"] == "UNRESOLVED"
    assert result["decision"]["original_quality_hold_remains"] is True
    assert result["access_boundary"]["other_biological_columns_used_in_statistics"] == 0
    assert "site_049" not in json.dumps(result)


def test_qc_detects_trivial_case_whitespace_without_claiming_repair():
    labels = [
        f"  {'SITE' if k%2 else 'site'}_{i:03d} {' ' * (k+1)}"
        for k in range(10) for i in range(1, 49)
    ]
    contract, fake_fetch = _fixture(labels)
    result = run_audit(contract, fake_fetch)
    assert result["status"] == "TRIM_CASE_LABEL_FORMAT_ONLY_POSSIBLE"
    summer = result["seasonal_identifier_summaries"]["summer"]
    assert summer["raw_unique_locationname_labels"] == 480
    assert summer["normalized_unique_locationname_labels"] == 48
    assert result["decision"]["physical_camera_identity_resolved"] is False


def test_qc_rejects_source_inconsistent_with_prior_filtered_434():
    contract, fake_fetch = _fixture([f"site_{i:03d}" for i in range(1, 49)])
    value = run_audit(contract, fake_fetch)
    assert value["status"] == "STOP_FROZEN_OUTCOME_SOURCE_MISMATCH"
    assert value["decision"]["original_quality_hold_remains"] is True


def test_qc_rejects_unpinned_bytes():
    contract, fake_fetch = _fixture([f"site_{i:03d}" for i in range(1, 435)])
    contract["inputs"][1]["git_blob_sha"] = "0" * 40
    with pytest.raises(ValueError, match="pinned source bytes"):
        run_audit(contract, fake_fetch)


def test_contract_is_postoutcome_not_response_blind_and_never_reclassifies():
    v = _contract()
    assert v["status"] == "FROZEN_EXPLORATORY_POSTOUTCOME_QC_NOT_AUTHORIZED"
    assert v["authorized_operations"]["download_entire_four_pinned_csv_files_in_memory"] is True
    assert v["authorized_operations"]["note_entire_source_CSVs_contain_biological_rows"] is True
    assert v["authorized_operations"]["project_only_LocationName_values_for_statistics"] is True
    assert v["authorized_operations"]["use_timestamps_or_species_or_event_outcomes"] is False
    assert v["authorized_operations"]["fit_refit_or_reclassify_original_model"] is False
    assert v["governance"]["original_outcome_status_frozen"] == "UNRESOLVED"
    assert v["governance"]["original_one_shot_rerun_authorized"] is False
    assert v["governance"]["metadata_only_claim_for_this_qc_forbidden"] is True
    assert v["decision_rules"]["regardless_of_result_original_quality_hold_cannot_be_lifted_by_this_diagnostic_alone"] is True


def test_qc_workflow_is_one_shot_and_uploads_aggregate_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "e5/wildpig-ca-locationname-qc-once-v1" in text
    assert "E5_WILDPIG_CA_LOCATIONNAME_QC_AUTHORIZED.json" in text
    assert "workflow_dispatch" not in text
    assert "audit_e5_wildpig_ca_locationname.py" in text
    assert "qc_result.json" in text
