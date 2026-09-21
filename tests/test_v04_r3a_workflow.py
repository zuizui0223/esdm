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
    assert "7fac98708d4474dc175d48c0ec3854f63d0ba527" in text
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
        "tests/test_v04_r3a_identification.py",
        "tests/test_v04_r3a_script.py",
        "tests/test_v04_r3a_workflow.py",
        "tests/test_v04_r2_identification.py",
    ):
        assert required in text
