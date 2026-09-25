from pathlib import Path


def test_v07b_gate_document_freezes_dynamic_recovery_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07B_DYNAMIC_RECOVERY_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.7b MCMC OUTCOME" in text
    assert "contexts **1-8**" in text
    assert "contexts **1-4**" in text
    assert "contexts **9-12**" in text
    assert "joint effort = **500**" in text
    assert "direct occupancy effort = **500**" in text
    assert "target-SD proxies are <= 0.25" in text
    assert "replicates = **16**" in text
    assert "total fits = **32**" in text
    assert "base seed = **20261117**" in text
    assert "seed stride = **113**" in text
    assert "warmup = **300**" in text
    assert "posterior samples = **350**" in text
    assert "chains = **2**" in text
    assert "abs(mean posterior bias) <= **0.20**" in text
    assert "empirical 90% interval coverage >= **0.75**" in text
    assert "14/16 = 0.875" in text
    assert "+0.50 nats/context" in text
    assert "divergences / 32 <= **0.10**" in text
