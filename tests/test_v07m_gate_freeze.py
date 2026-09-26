from pathlib import Path


def test_v07m_gate_document_freezes_absolute_adequacy_first_policy():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V07M_ABSOLUTE_ADEQUACY_POLICY_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE ANY v0.7m CONFIRMATORY MCMC OUTCOME" in text
    assert "absolute worst-dynamic-SD threshold = 0.35" in text
    assert "relative adaptive/transferred worst-dynamic-SD ratio threshold = 0.80" in text
    assert "if A > 0.35: abstain" in text
    assert "else if T > 0.35: adaptive" in text
    assert "else if R <= 0.80: adaptive" in text
    assert "else: transferred" in text
    assert "adaptive_absolute_rescue" in text
    assert "transfer_adequate" in text
    assert "abstain_inadequate" in text
    assert "total replicates = 64" in text
    assert "total fits = 192" in text
    assert "stride = 197" in text
    assert "absolute mean posterior bias <= 0.20" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "v0.7m remains an observation-design policy programme, not" in text
