from pathlib import Path


def test_r5b_gate_document_freezes_full_outcome_contract():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V04_R5B_OUTCOME_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R5b OUTCOME**" in text
    assert "R5a frozen result status: PASS" in text
    assert "16 independently generated replicates" in text
    assert "Total fits = 16 × 3 = 48" in text
    assert "base seed = 20260926" in text
    assert "seed stride = 47" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "credible mass = 0.90" in text
    assert "target accept probability = 0.90" in text
    assert "absolute mean posterior bias" in text and "0.18" in text
    assert "coverage" in text and "0.75" in text
    assert "mean activity_gain >= 0.005" in text
    assert "mean state_gain >= 0.005" in text
    assert "total divergences / 48 <= 0.10" in text
    assert "zero held-out east exposure" in text
