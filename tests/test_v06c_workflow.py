from pathlib import Path


def test_v06c_workflow_requires_explicit_authorization():
    text = (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v06c-alignment-stress-once.yml"
    ).read_text(encoding="utf-8")

    assert "V06C_RUN_AUTHORIZED" in text
    assert "needs.precheck.outputs.authorized == 'true'" in text
    precheck = text.split("\n  audit:\n", 1)[0]
    assert "python scripts/run_v06c_alignment_stress.py" not in precheck
