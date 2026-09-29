from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-reduced-result-import.yml"


def _text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_e3_result_import_catches_completion_and_merge_time_race():
    text = _text()

    assert "workflow_run:" in text
    assert "E3 MICA reduced exploratory fit once" in text
    assert "- completed" in text
    assert "push:" in text
    assert ".github/workflows/e3-mica-reduced-result-import.yml" in text
    assert "workflow_dispatch" not in text


def test_e3_result_import_uses_one_exact_frozen_execution_identity():
    text = _text()

    assert 'expected_run = int(frozen["workflow_run_id"])' in text
    assert 'expected_attempt = int(frozen["run_attempt"])' in text
    assert 'expected_head = str(frozen["authorization_head_sha"])' in text
    assert 'expected_branch = str(frozen["authorization_branch"])' in text
    assert 'int(run["id"]) == expected_run' in text
    assert 'int(run["run_attempt"]) == expected_attempt' in text
    assert 'str(run["head_sha"]) == expected_head' in text
    assert 'str(run["head_branch"]) == expected_branch' in text


def test_e3_result_import_skips_safely_when_merge_precedes_fit_completion():
    text = _text()

    assert 'completed = str(run.get("status")) == "completed"' in text
    assert "Authorized E3 fit is still running" in text
    assert "steps.guard.outputs.proceed == 'true'" in text


def test_e3_result_import_freezes_result_regardless_of_fit_workflow_conclusion():
    text = _text()

    assert "run_conclusion" in text
    assert "conclusion" not in text.split("proceed = bool(", 1)[1].split(")", 1)[0]
    assert "freeze_e3_mica_reduced_result.py" in text
    assert "E3_MICA_REDUCED_EMPIRICAL_RESULT.json" in text
    assert "E3_MICA_REDUCED_FROZEN_RESULT.json" in text
    assert "e3-mica-reduced-frozen-import-v1" in text


def test_e3_result_import_does_not_run_odsp_or_make_scientific_claims():
    text = _text()

    assert "odsp transfer" not in text
    assert "build_population_transfer_value_handoff" not in text
    assert "scripts/summarize_e3_mica_odsp_audit.py" not in text



def test_e3_result_import_allows_zero_or_one_canonical_artifact_only():
    text = _text()

    assert "if len(matches) > 1:" in text
    assert "available={'true' if len(matches) == 1 else 'false'}" in text
    assert "count={len(matches)}" in text


def test_e3_result_import_uses_scientific_receipt_when_artifact_exists():
    text = _text()

    assert "steps.artifact.outputs.available == 'true'" in text
    assert "freeze_e3_mica_reduced_result.py" in text
    assert "E3_MICA_REDUCED_FROZEN_RESULT.json" in text


def test_e3_result_import_freezes_infrastructure_stop_when_artifact_missing():
    text = _text()

    assert "steps.artifact.outputs.available != 'true'" in text
    assert "freeze_e3_mica_infrastructure_stop.py" in text
    assert "E3_MICA_REDUCED_INFRASTRUCTURE_STOP.json" in text
    assert "build/import/*.json" in text
