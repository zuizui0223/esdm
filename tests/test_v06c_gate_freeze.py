from pathlib import Path


def test_v06c_gate_freezes_budget_and_outcome_profile():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V06C_BUDGET_MATCHED_ACCESSIBILITY_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.6c QUALIFICATION OR MCMC OUTCOME" in text
    assert "12.168687798294679" in text
    assert "<= 1e-12" in text
    assert "<= 0.50" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261021" in text
    assert "seed stride = 101" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert ">= 0.875" in text
    assert "<= 0.75" in text
    assert "descriptively only" in text
