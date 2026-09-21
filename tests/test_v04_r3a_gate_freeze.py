from pathlib import Path


def test_r3a_gate_document_contains_exact_frozen_contract():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V04_R3A_QUALIFICATION_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R3a IDENTIFICATION OUTCOME**" in text
    assert "36 spatial sites × 12 temporal contexts" in text
    assert "432 state-annotation context opportunities" in text
    assert "18 sites × 24 temporal contexts" in text
    assert "13" in text and "identification targets" in text
    assert "Anchor A" in text and "Anchor B" in text and "Anchor C" in text
    assert "rtol = " in text and "1e-8" in text
    assert "atol = " in text and "1e-10" in text
    assert "relative minimum singular value >= " in text and "1e-3" in text
    assert "condition number <= " in text and "1e3" in text
    assert "target SD proxy <= " in text and "0.25" in text
    assert "Fisher ridge = " in text and "1e-10" in text
    assert "sparse practical refusal" in text
    assert "unknown annotated-detection refusal" in text
    assert "R3a contains no MCMC" in text
    assert "first 18" in text
    assert "Spatial distances are compared without tolerance quantization" in text
    assert "No threshold" in text or "no threshold" in text


def test_r3a_gate_document_freezes_exact_budget_counts_and_decision_terms():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V04_R3A_QUALIFICATION_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "annotated context count = 432" in text
    assert "annotated site count = 36" in text
    assert "annotated temporal-context count = 12" in text
    assert "calibrated PresenceOnly context count = 432" in text
    assert "first-18 prefix equality" in text
    assert "10 required terms" in text
