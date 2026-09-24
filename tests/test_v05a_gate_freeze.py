from pathlib import Path


def test_v05a_identification_gate_is_frozen_before_outcome():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05A_IDENTIFICATION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE v0.5a IDENTIFICATION OUTCOME**" in text
    assert "focal.partner_effect.beta_partner" in text
    assert "beta_partner = +0.80" in text
    assert "beta_partner = 0.0" in text
    assert "structural rtol = 1e-8" in text
    assert "structural atol = 1e-10" in text
    assert "relative minimum singular value >= 1e-3" in text
    assert "condition number <= 1e3" in text
    assert "target SD proxy <= 0.25" in text
    assert "No MCMC is allowed before all four terms pass" in text
    assert "PREDICTIVE_DEPENDENCE" in text
