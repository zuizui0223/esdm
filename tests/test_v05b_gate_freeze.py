from pathlib import Path


def test_v05b_gate_document_freezes_hidden_driver_stress_test():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05B_HIDDEN_DRIVER_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.5b OUTCOME" in text
    assert "beta_partner = 0.0" in text
    assert "source hidden slope = 0.90" in text
    assert "focal hidden slope = 1.00" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261005" in text
    assert "seed stride = 83" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "abs(mean fitted beta) <= 0.10" in text
    assert "coverage of beta=0 >= 0.75" in text
    assert "nonzero 90% interval rate <= 0.25" in text
    assert "gain <= 0.005" in text
    assert "total divergences / 32 <= 0.10" in text
