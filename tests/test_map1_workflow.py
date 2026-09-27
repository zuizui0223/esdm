from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "map1-qualification-once.yml"


def test_map1_workflow_is_separate_one_shot_branch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "map1/qualification-v1" in text
    assert "MAP1_RUN_AUTHORIZED" in text
    assert "workflow_dispatch" not in text
    assert "authorization commit must change only the marker" in text
    assert "implementation_parent_sha" in text
    assert "MAP1_QUALIFICATION_GATE_AMENDMENT_1.md" in text
    assert "MAP1 amendment mismatch" in text


def test_map1_workflow_contains_complete_frozen_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")
    for world in ("N0", "N1", "P1"):
        assert world in text
    for replicate in range(16):
        assert str(replicate) in text
    assert "max-parallel: 12" in text
    assert "scripts/run_map1_replicate.py" in text
    assert "scripts/aggregate_map1.py" in text
