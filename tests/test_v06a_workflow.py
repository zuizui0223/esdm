from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v06a-accessibility-once.yml"
    ).read_text(encoding="utf-8")


def test_v06a_workflow_qualifies_before_sixteen_replicates():
    text = _text()

    assert "qualification:" in text
    assert "needs: [precheck, qualification]" in text
    assert "needs.qualification.result == 'success'" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v06a_precheck_does_not_execute_scientific_outcome():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  qualification:\n", 1)[0]

    assert "run_v06a_qualification.py" not in precheck
    assert "run_v06a_replicate.py" not in precheck
    assert "aggregate_v06a.py" not in precheck
