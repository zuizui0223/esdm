from pathlib import Path


def test_v07f_gate_document_freezes_out_of_family_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07F_MISSPECIFIED_RESOLUTION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE HELD-OUT OUTCOME" in text
    assert "beta_gamma_time" not in text  # prose uses coefficient labels, not code names
    assert "colonization time coefficient = +0.55" in text
    assert "extinction time coefficient = -0.35" in text
    assert "cubic time slope = +0.35" in text
    assert "joint occurrence exposed for fitting at contexts 1-8 only" in text
    assert "direct OccupancyCount exposed at contexts 1-4 only" in text
    assert "contexts 9-12 used only for joint-occurrence scoring" in text
    assert "base seed = 20261217" in text
    assert "base seed = 20271217" in text
    assert "seed stride = 173" in text
    assert "replicates = 16" in text
    assert "total fits = 64" in text
    assert "rate >= 0.75" in text
    assert "mean correct-direction gain >= +0.25 nats" in text
    assert "divergences / fit <= 0.10" in text
