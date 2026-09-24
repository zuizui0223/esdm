from pathlib import Path


def test_r6_gate_document_freezes_matched_world_contract():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V04_R6_MATCHED_GATE.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE R6 OUTCOME**" in text
    assert "replicates per world = 16" in text
    assert "total fits = 64" in text
    assert "base seed = 20260924" in text
    assert "replicate stride = 61" in text
    assert "null-world seed offset = 1000000" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "chains = 2" in text
    assert "target accept probability = 0.90" in text
    assert "Material gain threshold = **0.005**" in text
    assert "proportion with resolution_gain > 0 >= 0.75" in text
    assert "mean resolution_gain >= 0.005" in text
    assert "mean resolution_gain <= 0.005" in text
    assert "proportion with resolution_gain > 0.005 <= 0.25" in text
    assert "total divergences / 64 <= 0.10" in text
    assert "zero east-heldout exposure" in text
