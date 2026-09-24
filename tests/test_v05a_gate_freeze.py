from pathlib import Path


def test_v05a_gate_document_freezes_full_two_world_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05A_DIRECTED_KNOWN_TRUTH_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.5a IDENTIFICATION OR MCMC OUTCOME" in text
    assert "beta_partner = +0.75" in text
    assert "beta_partner = 0.0" in text
    assert "target SD proxy <= 0.25" in text
    assert "replicates per world = 16" in text
    assert "total fits = 64" in text
    assert "base seed = 20261001" in text
    assert "seed stride = 73" in text
    assert "null-world offset = 1000000" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "abs(mean beta bias) <= 0.15" in text
    assert "abs(mean fitted beta) <= 0.10" in text
    assert "mean Full-minus-knockout held-out gain >= 0.005" in text
    assert "mean Full-minus-knockout held-out gain <= 0.005" in text
    assert "total divergences / 64 <= 0.10" in text
