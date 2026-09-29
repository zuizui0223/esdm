from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "e4-mica-sparse-fit-once.yml"


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_e4_fit_workflow_is_marker_only_and_one_shot():
    text = _text()
    trigger = text.split("\npermissions:\n", 1)[0]

    assert "e4/mica-sparse-fit-run-v1" in trigger
    assert "E4_MICA_SPARSE_FIT_AUTHORIZED.json" in trigger
    assert "E4_MICA_SPARSE_FIT_CONTRACT.json" not in trigger
    assert "workflow_dispatch" not in text
    assert "cancel-in-progress: false" in text
    assert "authorization must be marker-only" in text
    assert "implementation_parent_sha" in text


def test_e4_fit_workflow_pins_all_three_immutable_inputs():
    text = _text()

    assert "run-id: 36369531079" in text
    assert "run-id: 36399428007" in text
    assert "run-id: 36621160011" in text
    assert "2a8ce70ce8eefbbd70a2cdeaa2f4fc558aa64ab061985c263c8d1656979d83ff" in text


def test_e4_fit_workflow_preserves_result_on_stop():
    text = _text()

    assert "timeout-minutes: 240" in text
    assert "continue-on-error: true" in text
    assert "if: always()" in text
    assert "fit_e4_mica_sparse.py" in text
    assert "E4_MICA_SPARSE_EMPIRICAL_RESULT.json" in text
    assert "Preserve terminal scientific or execution stop as workflow failure" in text
