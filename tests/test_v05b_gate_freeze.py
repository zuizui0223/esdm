from pathlib import Path


def test_v05b_gate_is_frozen_before_identification_outcome():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05B_IDENTIFICATION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE v0.5b IDENTIFICATION OUTCOME**" in text
    assert "beta_partner = +0.80" in text
    assert "beta_partner = 0.0" in text
    assert "source_beta_perturbation = 1.0" in text
    assert "relative minimum singular value >= 1e-3" in text
    assert "condition number <= 1e3" in text
    assert "target SD proxy <= 0.25" in text
    assert "No MCMC is permitted before all four pass" in text
