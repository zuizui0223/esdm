from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v06c-budget-matched-accessibility-once.yml"
    ).read_text(encoding="utf-8")


def test_v06c_workflow_requires_qualification_before_replicates():
    text = _text()
    assert "V06C_RUN_AUTHORIZED" in text
    assert "needs.qualification.result == 'success'" in text
    assert "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]" in text
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
