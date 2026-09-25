from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07i-burned-pilot-once.yml"
    ).read_text(encoding="utf-8")


def test_v07i_workflow_runs_sixteen_three_fit_replicates():
    text = _text()

    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text
    assert "run_v07i_replicate.py" in text
    assert "aggregate_v07i.py" in text


def test_v07i_outcome_requires_explicit_authorization_marker():
    text = _text()

    assert "docs/validation/V07I_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]
    assert "run_v07i_replicate.py" not in precheck
    assert "aggregate_v07i.py" not in precheck


def test_v07i_cleanup_cannot_cancel_authorized_outcome():
    text = _text()

    assert "cancel-in-progress: false" in text


def test_v07i_aggregate_is_fail_closed():
    text = _text()

    assert '"status":"INFRASTRUCTURE_BLOCKED"' in text
    assert "if: always()" in text
