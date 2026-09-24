from pathlib import Path


def test_v06b_gate_freezes_control_diagnostics_and_interpretation_map():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V06B_JOINT_IDENTIFICATION_AUDIT.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.6b AUDIT OUTCOME" in text
    assert "9e1eba2c7efceec17b74dedc03a9db417381e831" in text
    assert "rank rtol = 1e-8" in text
    assert "rank atol = 1e-10" in text
    assert "target SD proxy threshold = 0.25" in text
    assert "Outcome A" in text
    assert "Outcome B" in text
    assert "Outcome C" in text
    assert "sufficient but not universally necessary" in text
