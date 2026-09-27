from pathlib import Path


def test_r4a_gate_document_contains_exact_frozen_contract():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V04_R4A_QUALIFICATION_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R4a IDENTIFICATION OUTCOME**" in text
    assert "36 spatial sites × 12 temporal contexts" in text
    assert "432 annotated context opportunities" in text
    assert "DOY 15, 135, 255" in text
    assert "0, 6, 12, 18" in text
    assert "13 targets" in text
    assert "Anchor A" in text and "Anchor B" in text and "Anchor C" in text
    assert "rtol = 1e-8" in text
    assert "atol = 1e-10" in text
    assert "relative minimum singular value >= 1e-3" in text
    assert "condition number <= 1e3" in text
    assert "target SD proxy <= 0.25" in text
    assert "Fisher ridge = 1e-10" in text
    assert "sparse practical refusal" in text
    assert "unknown annotated-detection refusal" in text
    assert "R4a contains no MCMC" in text
    assert "13 required terms" in text
