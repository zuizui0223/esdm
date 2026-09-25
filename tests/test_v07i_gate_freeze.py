from pathlib import Path


def test_v07i_gate_document_freezes_disjoint_burned_pilot_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07I_BURNED_PILOT_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER PRE-OUTCOME CI, BEFORE CONFIRMATORY OUTCOME" in text
    assert "contexts **1,2,3,4** only" in text
    assert "all **70 = choose(8,4)**" in text
    assert "generating truth" in text
    assert "not an input to the placement selector" in text
    assert "base seed = 20270105" in text
    assert "seed stride = 191" in text
    assert "base seed = 20280105" in text
    assert "seed stride = 193" in text
    assert "Replicates = 16" in text
    assert "total fits = 48" in text
    assert "rate >= 0.75" in text
    assert "ratio <= 0.90" in text
    assert "coverage >= 0.75" in text
    assert "divergences / fit <= 0.10" in text
    assert "held-out selected-minus-baseline" in text
    assert "not promotion criteria" in text
