from pathlib import Path


def test_v07l_gate_document_freezes_selective_policy():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07L_SELECTIVE_ADAPTATION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE ANY v0.7l CONFIRMATORY MCMC OUTCOME" in text
    assert "predicted adaptive/transferred worst-SD ratio <= 0.80" in text
    assert "strong_headroom trigger rate >= 0.75" in text
    assert "threshold_below trigger rate >= 0.75" in text
    assert "threshold_above trigger rate <= 0.25" in text
    assert "negligible_headroom trigger rate <= 0.25" in text
    assert "trigger sensitivity for actual material headroom >= 0.75" in text
    assert "trigger specificity >= 0.75" in text
    assert "balanced accuracy >= 0.75" in text
    assert "mean policy/transferred ratio <= 0.95" in text
    assert "policy harm rate" in text and "<= 0.10" in text
    assert "mean policy regret <= 0.05" in text
    assert "absolute mean posterior bias <= 0.20" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "total replicates = 64" in text
    assert "total fits = 192" in text
