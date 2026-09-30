from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication"
    / "E4_MICA_ODSP_LOCATION_BLOCK_SENSITIVITY_CONTRACT.json"
)
WORKFLOW = (
    ROOT / ".github" / "workflows"
    / "e4-mica-odsp-location-sensitivity.yml"
)


def test_location_block_sensitivity_boundary_is_postresult_and_nonpromoting():
    value = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert value["status"] == "POSTRESULT_DESCRIPTIVE_SENSITIVITY_FROZEN"
    sensitivity = value["sensitivity"]
    assert sensitivity["frozen_point_row_count"] == 733
    assert sensitivity["official_odsp_block"] == "deploymentID"
    assert sensitivity["sensitivity_block"] == "locationName"
    assert sensitivity["expected_location_block_count"] == 27
    assert sensitivity["deployment_weights_changed"] is False
    assert sensitivity["point_gain_must_remain_identical"] is True

    boundary = value["boundary"]
    assert boundary["replaces_official_733_block_audit"] is False
    assert boundary["changes_e4_decision"] is False
    assert boundary["superpopulation_interpretation_authorized"] is False
    assert boundary["n3_handoff_authorized"] is False
    assert boundary["confirmatory_claim"] is False
    assert boundary["causal_claim"] is False
    assert boundary["rerun_or_retuning_authorized"] is False


def test_location_block_workflow_uses_frozen_artifacts_and_pinned_odsp_only():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "run-id: 36622802225" in text
    assert "run-id: 36369531079" in text
    assert "34124094e6c25db04465cc1ff869af5813326729e6fd3b658a0921c45bc6f3e2" in text
    assert "0bd83e1ebb372c48839654ab0e42124fe37b8faf" in text
    assert "export_e4_mica_odsp_location_blocks.py" in text
    assert "summarize_e4_mica_odsp_location_sensitivity.py" in text
    assert "odsp transfer" in text

    for forbidden in (
        "fit_numpyro",
        "fit_e4_mica_sparse",
        "num_warmup",
        "num_samples",
        "workflow_dispatch",
    ):
        assert forbidden not in text
