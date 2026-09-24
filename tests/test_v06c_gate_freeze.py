from pathlib import Path


def test_v06c_gate_freezes_alignment_and_primary_checks():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V06C_ALIGNMENT_STRESS_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.6c AUDIT OUTCOME" in text
    assert "6c5641944a0a3cd112b718bc5d949607b5b52e37" in text
    for value in ("0.00", "0.50", "0.90", "0.99"):
        assert f"rho = {value}" in text
    assert "target SD proxy threshold = 0.25" in text
    assert "Direct-calibrated has all four targets" in text
    assert "At rho = 0.99" in text
