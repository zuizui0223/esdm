from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "field1-qualification-once.yml"
MARKER = ROOT / "docs" / "field" / "FIELD1_RUN_AUTHORIZED"


def test_field1_workflow_is_one_shot_and_not_currently_authorized():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "FIELD1_RUN_AUTHORIZED" in text
    assert "workflow_dispatch" not in text
    assert "fetch-depth: 2" in text
    assert "--diff-filter=A" in text
    assert "marker was not newly added" in text
    assert not MARKER.exists()


def test_field1_workflow_freezes_complete_world_replicate_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")

    for world in (
        "K0",
        "K1",
        "K2",
        "K3",
        "K4",
        "K5_mean0_cov0",
        "K5_mean1_cov0",
        "K5_mean0_cov1",
        "K5_mean1_cov1",
    ):
        assert f"- {world}" in text

    for replicate in range(16):
        assert f"- {replicate}" in text

    assert "max-parallel: 12" in text
    assert "scripts/run_field1_replicate.py" in text
    assert "scripts/aggregate_field1.py" in text
    assert "merge-multiple: false" in text



def test_field1_workflow_preserves_infrastructure_blocked_receipt():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "continue-on-error: true" in text
    assert '"status": "INFRASTRUCTURE_BLOCKED"' in text
    assert '"scientific_decision": None' in text
    assert "if: always()" in text
