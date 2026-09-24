from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v05c-event-gated-once.yml"
    ).read_text(encoding="utf-8")


def test_v05c_workflow_crosses_two_worlds_by_sixteen_replicates():
    text = _text()

    assert "world: [interaction_event, hidden_driver_null]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
    assert "aggregate_v05c.py" in text


def test_v05c_precheck_does_not_execute_outcome():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "python scripts/run_v05c_replicate.py" not in precheck
    assert "python scripts/aggregate_v05c.py" not in precheck
