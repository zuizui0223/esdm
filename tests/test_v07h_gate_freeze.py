from pathlib import Path


def test_v07h_gate_freezes_expected_count_matched_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07H_EXPECTED_RECORD_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER DETERMINISTIC EXPECTED-COUNT CONTROL, BEFORE MCMC OUTCOME" in text
    assert "placement = (1,2,3,4)" in text
    assert "placement = (2,6,7,8)" in text
    assert "effort per direct context = 369.15453700836173" in text
    assert "baseline = 931.2500000000001" in text
    assert "selected = 931.25" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20270105" in text
    assert "seed stride = 181" in text
    assert "rate >= 0.75" in text
    assert "mean selected/baseline worst-SD ratio <= 0.90" in text
    assert "absolute mean posterior bias <= 0.15" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "divergences / fit <= 0.10" in text
