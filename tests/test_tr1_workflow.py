from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tr1-trait-transfer-once.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_tr1_workflow_requires_explicit_authorization_and_has_no_manual_dispatch():
    text = _text()

    assert "TR1_RUN_AUTHORIZED" in text
    assert "tr1/trait-transfer-run-v1" in text
    assert "feature/tr1-trait-transfer-gate-clean" not in text
    assert "authorized == 'true'" in text
    assert "workflow_dispatch" not in text
    assert "authorization commit must change only the marker" in text
    assert "implementation_parent_sha" in text
    assert "abd3056006adf6c72d73188e8d43e5d9c8ff306a" in text


def test_tr1_precheck_does_not_execute_frozen_outcome():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "run_tr1_replicate.py" not in precheck
    assert "aggregate_tr1.py" not in precheck


def test_tr1_workflow_runs_exact_positive_and_null_replication_family():
    text = _text()

    assert "world: [positive, null]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]"
        in text
    )
    assert "max-parallel: 32" in text
    assert "fail-fast: false" in text


def test_tr1_odsp_export_occurs_only_after_completed_aggregate_result():
    text = _text()

    assert "TR1_RESULT_V1.json" in text
    assert 'result.get("status") == "PASS"' in text
    assert "export_tr1_odsp_transfer.py" in text
    assert "Preserve scientific FAIL as workflow failure" in text


def test_tr1_trigger_listens_only_to_marker_on_dedicated_run_branch():
    text = _text()
    trigger = text.split("\npermissions:\n", 1)[0]

    assert "tr1/trait-transfer-run-v1" in trigger
    assert "docs/validation/TR1_RUN_AUTHORIZED" in trigger
    assert "TR1_TRAIT_TRANSFER_CONTRACT_V1.json" not in trigger
    assert "src/esdm/validate/tr1_trait_transfer.py" not in trigger
    assert "scripts/run_tr1_replicate.py" not in trigger
