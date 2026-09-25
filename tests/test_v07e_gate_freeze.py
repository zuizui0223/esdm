from pathlib import Path


def test_v07e_gate_document_freezes_reciprocal_specificity_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07E_RECIPROCAL_STATIC_WORLD_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER PRE-OUTCOME QUALIFICATION, BEFORE HELD-OUT OUTCOME" in text
    assert "base seed = 20261217" in text
    assert "seed stride = 173" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "Static > Dynamic in at least 14/16 replicates" in text
    assert "mean Static-minus-Dynamic gain >= +0.50" in text
    assert "4 versus 4" in text
    assert "generator is exactly the v0.7d equal-dimension static quadratic" in text
