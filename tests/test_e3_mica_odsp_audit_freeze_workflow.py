from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-odsp-audit-result-freeze.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_e3_audit_freeze_only_listens_to_postresult_audit_workflow():
    text = _text()

    assert "workflow_run:" in text
    assert "E3 MICA post-result ODSP audit" in text
    assert "workflow_dispatch" not in text


def test_e3_audit_freeze_only_accepts_main_push_audit_run():
    text = _text()

    assert "github.event.workflow_run.event == 'push'" in text
    assert "github.event.workflow_run.head_branch == 'main'" in text
    assert "e3-mica-odsp-postresult-audit-v1" in text


def test_e3_audit_freeze_pins_artifact_digest_and_head_sha():
    text = _text()

    assert "--artifact-digest" in text
    assert "digest={digest}" in text
    assert "workflow_run.head_sha" in text
    assert "freeze_e3_mica_odsp_audit_result.py" in text
    assert "E3_MICA_ODSP_AUDIT_FROZEN_RESULT.json" in text


def test_e3_audit_freeze_does_not_rerun_odsp():
    text = _text()

    assert "odsp transfer" not in text
    assert "scripts/export_e3_mica_odsp_parallel.py" not in text
