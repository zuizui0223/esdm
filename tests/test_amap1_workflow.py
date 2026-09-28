from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "amap1-qualification-once.yml"


def test_amap1_workflow_is_separate_one_shot_branch():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "amap1/qualification-v1" in text
    assert "AMAP1_RUN_AUTHORIZED" in text
    assert "workflow_dispatch" not in text
    assert "fetch-depth: 2" in text
    assert "--diff-filter=A" in text
    assert "authorization commit must change only the marker" in text
    assert "implementation_parent_sha" in text
    assert "AMAP1_QUALIFICATION_GATE.md" in text
    assert "AMAP1 gate mismatch" in text


def test_amap1_workflow_contains_complete_frozen_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")

    for geometry in ("G1", "G2", "G3"):
        for truth in ("T0", "TX", "TC"):
            assert f"- {geometry}_{truth}" in text

    for replicate in range(16):
        assert f"- {replicate}" in text

    assert "max-parallel: 12" in text
    assert "scripts/run_amap1_replicate.py" in text
    assert "scripts/aggregate_amap1.py" in text
    assert "tests/test_amap1_aggregate.py" in text
    assert "merge-multiple: false" in text


def test_amap1_workflow_preserves_infrastructure_receipt_path():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "continue-on-error: true" in text
    assert "if: always()" in text
    assert "AMAP1_QUALIFICATION_RESULT.json" in text
