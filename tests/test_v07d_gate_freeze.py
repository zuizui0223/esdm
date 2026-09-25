from pathlib import Path


def test_v07d_gate_document_freezes_equal_dimension_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07D_EQUAL_DIMENSION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER PRE-OUTCOME QUALIFICATION, BEFORE HELD-OUT OUTCOME" in text
    assert "joint occurrence is exposed for fitting at contexts 1-8 only" in text
    assert "direct OccupancyCount is exposed at contexts 1-4 only" in text
    assert "contexts 9-12 are used only for joint-occurrence scoring" in text
    assert "direct occupancy exposure in contexts 9-12 is exactly zero" in text
    assert "both models contain exactly four free ecological parameters" in text
    assert "quadratic time slope" in text
    assert "target-SD threshold = 0.25" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261201" in text
    assert "seed stride = 163" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "rate >= 0.875" in text
    assert "mean dynamic-minus-static gain >= +0.50 nats" in text
    assert "divergences / fit <= 0.10" in text
