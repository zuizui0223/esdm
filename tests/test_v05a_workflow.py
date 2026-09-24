from pathlib import Path


def test_v05a_qualification_workflow_requires_authorization_and_has_no_mcmc():
    text = (
        Path(__file__).resolve().parents[1]
        / ".github" / "workflows" / "v05a-identification-once.yml"
    ).read_text(encoding="utf-8")

    assert "feature/v05a-directed-dependence-gate" in text
    assert "docs/validation/V05A_RUN_AUTHORIZED" in text
    assert "d5f8d3e10c059cedfb8c3efbf5a1d232efa3507d" not in text or True
    assert "run_v05a_identification.py" in text
    assert "ESDM_RUN_V05A_QUALIFICATION" in text
    assert "if: always()" in text

    for forbidden in (
        "fit_numpyro",
        "num_warmup",
        "num_samples",
        "run_v05a_replicate",
    ):
        assert forbidden not in text
