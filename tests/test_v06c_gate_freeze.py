from pathlib import Path


def test_v06c_gate_freezes_finite_frontier():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V06C_ACCESSIBILITY_FRONTIER_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.6c FRONTIER OUTCOME" in text
    assert "d725265751d7085d05d8d82bc83e32f810ef6f0a" in text
    assert "Exactly 9 cells" in text
    assert "distinct" in text
    assert "aligned" in text
    assert "flat_access" in text
    assert "-2.0" in text
    assert "+0.40" in text
    assert "+2.0" in text
    assert "effort = 8.0" in text
    assert "direct accessibility effort = 20.0" in text
    assert "target SD proxy threshold = 0.25" in text
    assert "There is no pass target" in text
