from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07e-reciprocal-static-world-once.yml"
    ).read_text(encoding="utf-8")


def test_v07e_workflow_requires_authorization_before_outcome():
    text = _text()

    assert "V07E_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "qualification:" in text
    assert "needs: [precheck, qualification]" in text
    assert "needs.qualification.result == 'success'" in text


def test_v07e_workflow_runs_exactly_sixteen_paired_replicates():
    text = _text()

    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v07e_precheck_does_not_open_outcome():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  qualification:\n", 1)[0]

    assert "run_v07e_qualification.py" not in precheck
    assert "run_v07e_replicate.py" not in precheck
    assert "aggregate_v07e.py" not in precheck
