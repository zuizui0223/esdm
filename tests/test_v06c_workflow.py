from pathlib import Path


def test_v06c_workflow_requires_authorization():
    text = (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v06c-accessibility-frontier-once.yml"
    ).read_text(encoding="utf-8")

    assert "V06C_RUN_AUTHORIZED" in text
    assert "needs.precheck.outputs.authorized == 'true'" in text
    precheck = text.split("\n  frontier:\n", 1)[0]
    assert "python scripts/run_v06c_frontier.py" not in precheck
