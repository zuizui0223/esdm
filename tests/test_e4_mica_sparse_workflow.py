from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    ROOT / ".github" / "workflows" / "e4-mica-sparse-qualification-once.yml"
)


def _text():
    return WORKFLOW.read_text(encoding="utf-8")


def test_e4_qualification_has_dedicated_marker_only_trigger():
    text = _text()
    trigger = text.split("\npermissions:\n", 1)[0]

    assert "e4/mica-sparse-qualification-v1" in trigger
    assert "E4_MICA_SPARSE_QUALIFICATION_AUTHORIZED.json" in trigger
    assert "E4_MICA_SPARSE_NUTS_CONTRACT.json" not in trigger
    assert "workflow_dispatch" not in text
    assert "cancel-in-progress: false" in text


def test_e4_qualification_verifies_pure_authorization():
    text = _text()

    assert "authorization must be marker-only" in text
    assert "implementation_parent_sha" in text
    assert '"E4_MICA_SPARSE_NUTS"' in text
    assert '"e4-mica-exact-sparse-nuts-v1"' in text
    assert "empirical_fit_authorized" in text


def test_e4_qualification_uses_immutable_e2_e3_artifacts_and_does_not_fit():
    text = _text()

    assert "run-id: 36369531079" in text
    assert "run-id: 36399428007" in text
    assert "qualify_e4_mica_sparse.py" in text
    assert "fit_e4_mica_sparse_nuts" not in text
    assert "fit_numpyro" not in text
    assert "num_warmup" not in text
    assert "num_samples" not in text
    assert "heldout_log_score" not in text
