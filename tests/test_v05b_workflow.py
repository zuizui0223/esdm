from pathlib import Path


def test_v05b_workflow_requires_authorization_and_has_no_mcmc():
    text = (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v05b-identification-once.yml"
    ).read_text(encoding="utf-8")

    assert "feature/v05b-source-perturbation-gate" in text
    assert "docs/validation/V05B_RUN_AUTHORIZED" in text
    assert "ESDM_RUN_V05B_QUALIFICATION" in text
    assert "run_v05b_identification.py" in text
    assert "if: always()" in text

    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "run_v05a_replicate",
    ):
        assert forbidden not in text
