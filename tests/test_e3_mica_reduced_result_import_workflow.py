from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-reduced-result-import.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_e3_result_import_is_bound_to_completed_fit_workflow_only():
    text = _text()

    assert "workflow_run:" in text
    assert "E3 MICA reduced exploratory fit once" in text
    assert "types:" in text
    assert "- completed" in text
    assert "workflow_dispatch" not in text


def test_e3_result_import_checks_exact_frozen_run_attempt_head_and_branch():
    text = _text()

    assert "workflow_run id is not the frozen E3 execution" in text
    assert "workflow_run attempt drifted" in text
    assert "workflow_run head SHA drifted" in text
    assert "workflow_run branch drifted" in text
    assert "E3_MICA_REDUCED_RESULT_IMPORT_CONTRACT.json" in text


def test_e3_result_import_freezes_result_regardless_of_fit_workflow_conclusion():
    text = _text()

    assert "github.event.workflow_run.conclusion" not in text
    assert "freeze_e3_mica_reduced_result.py" in text
    assert "E3_MICA_REDUCED_EMPIRICAL_RESULT.json" in text
    assert "E3_MICA_REDUCED_FROZEN_RESULT.json" in text
    assert "e3-mica-reduced-frozen-import-v1" in text


def test_e3_result_import_does_not_run_odsp_or_make_scientific_claims():
    text = _text()

    assert "odsp transfer" not in text
    assert "build_population_transfer_value_handoff" not in text
    assert "scripts/summarize_e3_mica_odsp_audit.py" not in text
