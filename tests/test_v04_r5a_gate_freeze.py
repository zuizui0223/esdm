from pathlib import Path


def test_r5a_gate_document_contains_exact_frozen_contract():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V04_R5A_QUALIFICATION_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R5a IDENTIFICATION OUTCOME**" in text
    assert "StateCompositionCount" in text
    assert "label_effort = 1.0" in text
    assert "total expected direct state labels = 432.0" in text
    assert "held-out direct-calibration context count = 0" in text
    assert "consumes exactly `state`" in text
    assert "13 R2/R3a/R4a targets" in text
    assert "Anchor A" in text and "Anchor B" in text and "Anchor C" in text
    assert "rtol = 1e-8" in text
    assert "atol = 1e-10" in text
    assert "relative minimum singular value >= 1e-3" in text
    assert "condition number <= 1e3" in text
    assert "target SD proxy <= 0.25" in text
    assert "Fisher ridge = 1e-10" in text
    assert "R5a contains no MCMC" in text
    assert "twelve required terms" in text
