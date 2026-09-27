from pathlib import Path


def test_r5a_workflow_requires_explicit_authorization_and_has_no_mcmc():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r5a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "feature/v04-r5-direct-state-calibration" in text
    assert "docs/validation/V04_R5A_RUN_AUTHORIZED" in text
    assert "d013b5168d7d10848d1d366669d45f83f873692a" in text
    assert "e5cef8c3ce8e1dd096ef45cc436a93ba6740bafb" in text
    assert "needs: precheck" in text
    assert "if: needs.precheck.outputs.authorized == 'true'" in text
    assert "run_v04_r5a_qualification.py" in text
    assert "INFRASTRUCTURE_BLOCKED" in text
    assert "if: always()" in text

    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "run_v04_r5a_replicate",
    ):
        assert forbidden not in text


def test_r5a_precheck_does_not_execute_identification_outcome():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r5a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "tests/test_v04_r5a_identification.py" not in text


def test_r5a_identification_test_requires_explicit_outcome_environment():
    path = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "test_v04_r5a_identification.py"
    )
    text = path.read_text(encoding="utf-8")

    assert "ESDM_RUN_R5A_QUALIFICATION" in text
