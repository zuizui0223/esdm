from pathlib import Path


def _workflow_text():
    return (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v05f-interaction-transfer-once.yml"
    ).read_text(encoding="utf-8")


def test_v05f_workflow_requires_explicit_authorization_before_science():
    text = _workflow_text()

    assert "V05F_RUN_AUTHORIZED" in text
    assert "authorized == 'true'" in text
    assert "qualification:" in text
    assert "replicate:" in text
    assert "aggregate:" in text


def test_v05f_workflow_runs_both_frozen_worlds_and_sixteen_replicates():
    text = _workflow_text()

    assert "world: [interaction, measured_shared_null]" in text
    assert (
        "replicate: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]"
        in text
    )
    assert "max-parallel: 16" in text
    assert "fail-fast: false" in text


def test_v05f_precheck_never_opens_mcmc_outcome_without_marker():
    text = _workflow_text()
    jobs = text.split("\njobs:\n", 1)[1]
    precheck = jobs.split("\n  qualification:\n", 1)[0]

    assert "run_v05f_qualification.py" not in precheck
    assert "run_v05f_replicate.py" not in precheck
    assert "aggregate_v05f.py" not in precheck


def test_v05f_workflow_exports_absolute_score_result_to_odsp_bundle():
    text = _workflow_text()

    assert "export_v05f_odsp_transfer.py" in text
    assert "artifacts/odsp-transfer/" in text
    assert "v05f_result.json" in text
