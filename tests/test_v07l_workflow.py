from pathlib import Path


def _text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v07l-selective-adaptation-once.yml"
    ).read_text(encoding="utf-8")


def test_v07l_workflow_requires_explicit_authorization():
    text = _text()

    assert "V07L_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "workflow_dispatch" not in text


def test_v07l_precheck_does_not_execute_confirmatory_mcmc():
    text = _text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  replicate:\n", 1)[0]

    assert "run_v07l_replicate.py" not in precheck
    assert "aggregate_v07l.py" not in precheck


def test_v07l_workflow_runs_exact_four_by_sixteen_fresh_pairs():
    text = _text()

    assert "strong_headroom" in text
    assert "threshold_below" in text
    assert "threshold_above" in text
    assert "negligible_headroom" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v07l_workflow_has_no_odsp_export_or_eog_action():
    text = _text()

    assert "odsp transfer" not in text
    assert "export_v07" not in text
    assert "EOG" not in text
