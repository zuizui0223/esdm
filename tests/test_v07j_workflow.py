from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07j-population-shift-once.yml"
    ).read_text(encoding="utf-8")


def test_v07j_workflow_requires_explicit_authorization():
    text = _text()

    assert "V07J_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text


def test_v07j_workflow_runs_exact_three_by_twelve_matrix():
    text = _text()

    assert "world: [low_occupancy, high_occupancy, high_turnover]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]"
        in text
    )
    assert "max-parallel: 18" in text
    assert "fail-fast: false" in text


def test_v07j_precheck_does_not_execute_mcmc():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "run_v07j_replicate.py" not in precheck
    assert "aggregate_v07j.py" not in precheck


def test_v07j_workflow_does_not_export_odsp_transfer():
    text = _text()

    assert "export_v07" not in text
    assert "odsp transfer" not in text
    assert "N2_TO_N3" not in text
