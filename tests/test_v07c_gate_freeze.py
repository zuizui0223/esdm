from pathlib import Path


def test_v07c_gate_document_freezes_matched_static_dynamic_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07C_STATIC_DYNAMIC_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE QUALIFICATION OR HELD-OUT OUTCOME" in text
    assert "joint occurrence is exposed for fitting at contexts 1-8 only" in text
    assert "direct OccupancyCount is exposed at contexts 1-4 only" in text
    assert "contexts 9-12 are used only for joint-occurrence scoring" in text
    assert "direct occupancy exposure in contexts 9-12 is exactly zero" in text
    assert "static model has three ecological parameters" in text
    assert "dynamic model has four ecological parameters" in text
    assert "target-SD threshold = 0.25" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261123" in text
    assert "seed stride = 157" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "rate >= 0.875" in text
    assert "mean dynamic-minus-static gain >= +0.50 nats" in text
    assert "divergences / fit <= 0.10" in text
