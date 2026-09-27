from pathlib import Path


def test_r3a_workflow_requires_explicit_authorization_and_has_no_mcmc():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r3a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "feature/v04-r3-budget-neutral-design" in text
    assert "docs/validation/V04_R3A_RUN_AUTHORIZED" in text
    assert "aa38b790e094261addd07c301edc24afa110cb4c" in text
    assert "ed470d4f6166c5107aeda9432ca44a985cb55e72" in text
    assert "needs: precheck" in text
    assert "if: needs.precheck.outputs.authorized == 'true'" in text
    assert "run_v04_r3a_qualification.py" in text
    assert "INFRASTRUCTURE_BLOCKED" in text
    assert "if: always()" in text

    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "run_v04_r3a_replicate",
    ):
        assert forbidden not in text


def test_r3a_workflow_precheck_covers_design_gate_and_refusal_contracts():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r3a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    for required in (
        "tests/test_v04_r3a_selectors.py",
        "tests/test_v04_r3a_fixture.py",
        "tests/test_v04_r3a_gate.py",
        "tests/test_v04_r3a_gate_freeze.py",
        "tests/test_v04_r3a_script.py",
        "tests/test_v04_r3a_workflow.py",
        "tests/test_v04_r2_identification.py",
    ):
        assert required in text



def test_r3a_precheck_does_not_execute_identification_outcome_before_authorization():
    path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "v04-r3a-qualification-once.yml"
    )
    text = path.read_text(encoding="utf-8")

    assert "tests/test_v04_r3a_identification.py" not in text



def test_r3a_identification_test_requires_explicit_outcome_environment():
    path = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "test_v04_r3a_identification.py"
    )
    text = path.read_text(encoding="utf-8")

    assert "ESDM_RUN_R3A_QUALIFICATION" in text
