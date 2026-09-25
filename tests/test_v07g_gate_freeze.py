from pathlib import Path


def test_v07g_gate_document_freezes_precision_validation():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07G_CALIBRATION_PLACEMENT_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER DETERMINISTIC DESIGN SELECTION, BEFORE MCMC OUTCOME" in text
    assert "contexts = (2, 6, 7, 8)" in text
    assert "contexts = (1, 2, 3, 4)" in text
    assert "total direct effort = 2000" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261225" in text
    assert "seed stride = 179" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "rate >= 0.75" in text
    assert "mean optimized/baseline worst-SD ratio <= 0.85" in text
    assert "absolute mean posterior bias <= 0.15" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "divergences / fit <= 0.10" in text
    assert "descriptively only" in text
