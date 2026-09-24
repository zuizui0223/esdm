from pathlib import Path


def test_v05b_gate_document_freezes_hidden_driver_stress():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05B_HIDDEN_COMMON_DRIVER_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.5b OUTCOME" in text
    assert "beta_partner = 0.0" in text
    assert "0.80 * source_driver_i" in text
    assert "0.65 * sin(2*pi*i/13)" in text
    assert "0.30 * cos(2*pi*i/5)" in text
    assert "hidden shared slope = 0.90" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261005" in text
    assert "seed stride = 79" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "abs(mean fitted beta) <= 0.10" in text
    assert "90% zero coverage >= 0.75" in text
    assert "nonzero 90% interval rate <= 0.25" in text
    assert "mean Full-minus-knockout held-out gain <= 0.005" in text
    assert "held-out gain > 0.005 <= 0.25" in text
    assert "mean divergences per fit <= 0.10" in text
