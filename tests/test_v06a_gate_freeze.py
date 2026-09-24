from pathlib import Path


def test_v06a_gate_document_freezes_accessibility_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V06A_ACCESSIBILITY_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.6a IDENTIFICATION OR MCMC OUTCOME" in text
    assert "effort = 20.0 in the first 24 training contexts" in text
    assert "zero held-out exposure" in text
    assert "target SD proxy <= 0.25" in text
    assert "must return exact-JAX `NotIdentified`" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261013" in text
    assert "seed stride = 89" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "abs(mean posterior bias) <= 0.15" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "Full > accessibility knockout in >= 75% of replicates" in text
    assert "held-out log-score gain >= 0.005" in text
    assert "total divergences / 32 <= 0.10" in text
