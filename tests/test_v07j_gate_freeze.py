from pathlib import Path


def test_v07j_gate_text_freezes_population_shift_design():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07J_POPULATION_SHIFT_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE ANY v0.7j OUTCOME" in text
    assert "selected placement = (2, 6, 7, 8)" in text
    assert "baseline placement = (1, 2, 3, 4)" in text
    assert "Low-occupancy target" in text
    assert "High-occupancy target" in text
    assert "High-turnover target" in text
    assert "replicates = 12" in text
    assert "total fits across three target worlds = 72" in text
    assert "at least 9/12 pairs" in text
    assert "mean selected/baseline worst-SD ratio <= 0.95" in text
    assert "absolute mean bias <= 0.20" in text
    assert "empirical 90% interval coverage >= 2/3" in text
    assert "a new ODSP information-transfer level" in text
