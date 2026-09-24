from pathlib import Path


def test_r7_gate_document_freezes_equal_budget_contract():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V04_R7_BUDGET_MATCHED_GATE.md"
    ).read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R7 OUTCOME**" in text
    assert "total expected direct state labels = 432.0" in text
    assert "total expected passive labels = 432.0" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20260928" in text
    assert "seed stride = 67" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "target accept probability = 0.90" in text
    assert "heldout_gain > 0 in >= 75% of replicates" in text
    assert "mean heldout_gain >= 0.005" in text
    assert "state_error_gain > 0 in >= 75% of replicates" in text
    assert "mean state_error_gain > 0" in text
    assert "absolute tolerance 1e-8" in text
    assert "total divergences / 32 <= 0.10" in text
