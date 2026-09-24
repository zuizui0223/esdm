from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v04-r7-budget-matched-once.yml"
    ).read_text(encoding="utf-8")


def test_r7_workflow_has_sixteen_paired_replicates():
    text = _text()

    assert "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]" in text
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
    assert "aggregate_v04_r7.py" in text
    assert "actions/download-artifact@v4" in text


def test_r7_precheck_does_not_execute_outcome_commands():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "python scripts/run_v04_r7_replicate.py" not in precheck
    assert "python scripts/aggregate_v04_r7.py" not in precheck
