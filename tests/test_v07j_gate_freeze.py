from pathlib import Path


def test_v07j_gate_document_freezes_population_shift_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07J_POPULATION_SHIFT_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER DETERMINISTIC SURFACE, BEFORE CONFIRMATORY MCMC OUTCOME" in text
    assert "psi0 = 0.20" in text
    assert "gamma = 0.15" in text
    assert "epsilon = 0.05" in text
    assert "psi0 = 0.80" in text
    assert "epsilon = 0.30" in text
    assert "rate >= 0.75" in text
    assert "mean selected/baseline ratio <= 0.95" in text
    assert "mean selected/baseline ratio >= 1.10" in text
    assert "base seed = 20261301" in text
    assert "base seed = 20271301" in text
    assert "seed stride = 179" in text
    assert "total fits = 64" in text
    assert "divergences / fit <= 0.10" in text
