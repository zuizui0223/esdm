from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v05b-hidden-driver-once.yml"
    ).read_text(encoding="utf-8")


def test_v05b_workflow_runs_sixteen_stress_replicates():
    text = _text()

    assert "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]" in text
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
    assert "aggregate_v05b.py" in text


def test_v05b_precheck_does_not_execute_outcome():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "python scripts/run_v05b_replicate.py" not in precheck
    assert "python scripts/aggregate_v05b.py" not in precheck
