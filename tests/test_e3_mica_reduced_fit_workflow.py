from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e3-mica-reduced-fit-once.yml"


def test_e3_reduced_fit_workflow_requires_pure_marker():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "explore/e3-mica-reduced-fit-run-v1" in text
    assert "E3_MICA_REDUCED_FIT_AUTHORIZED.json" in text
    assert "authorization must be a pure marker commit" in text
    assert "workflow_dispatch" not in text


def test_e3_reduced_fit_workflow_uses_only_immutable_captures():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "e2-mica-full-response-capture-36369531079" in text
    assert "run-id: 36369531079" in text
    assert "e3-mica-exploratory-capture-36399428007" in text
    assert "run-id: 36399428007" in text
    assert "curl" not in text


def test_e3_reduced_fit_workflow_runs_only_frozen_three_fit_script():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "fit_e3_mica_reduced.py" in text
    assert "--archive captured/e2/build/e2/source/mica-v3.zip" in text
    assert "--capture captured/e3/E3_MICA_EXPLORATORY_CAPTURE_RESULT.json" in text
    assert "E3_MICA_REDUCED_EMPIRICAL_RESULT.json" in text
