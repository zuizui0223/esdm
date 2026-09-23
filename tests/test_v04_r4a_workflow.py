from pathlib import Path


def test_r4a_workflow_requires_explicit_authorization_and_has_no_mcmc():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r4a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "feature/v04-r4-factorial-time-balance" in text
    assert "docs/validation/V04_R4A_RUN_AUTHORIZED" in text
    assert "65115f31425d4d8655137eeea9a0bdb40f56aa53" in text
    assert "c55af9dfbc6347218fecebb27542ee7bb59310b0" in text
    assert "needs: precheck" in text
    assert "if: needs.precheck.outputs.authorized == 'true'" in text
    assert "run_v04_r4a_qualification.py" in text
    assert "INFRASTRUCTURE_BLOCKED" in text
    assert "if: always()" in text

    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "run_v04_r4a_replicate",
    ):
        assert forbidden not in text


def test_r4a_precheck_does_not_execute_identification_outcome():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r4a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "tests/test_v04_r4a_identification.py" not in text


def test_r4a_identification_test_requires_explicit_outcome_environment():
    path = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "test_v04_r4a_identification.py"
    )
    text = path.read_text(encoding="utf-8")

    assert "ESDM_RUN_R4A_QUALIFICATION" in text
