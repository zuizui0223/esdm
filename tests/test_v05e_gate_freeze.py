from pathlib import Path


def test_v05e_gate_document_freezes_evidence_separation_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05E_EVIDENCE_SEPARATION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.5e OUTCOME" in text
    assert "event_intercept = -8.0" in text
    assert "event_intercept = -1.0" in text
    assert "true beta_partner = +0.75" in text
    assert "replicates per world = 16" in text
    assert "total fits = 48" in text
    assert "base seed = 20261009" in text
    assert "seed stride = 83" in text
    assert "realized_only offset = 1000000" in text
    assert "directed_realized offset = 2000000" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "positive pair-event rate <= 0.25" in text
    assert "PREDICTIVE_DEPENDENCE authorization rate >= 0.75" in text
    assert "positive pair-event rate >= 0.875" in text
    assert "REALIZED authorization rate >= 0.875" in text
    assert "abs(mean beta bias) <= 0.15" in text
    assert "abs(mean event-intercept bias) <= 0.30" in text
    assert "FUNCTIONAL-or-higher authorization rate = 0" in text
    assert "total divergences / 48 <= 0.10" in text
