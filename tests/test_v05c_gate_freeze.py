from pathlib import Path


def test_v05c_gate_document_freezes_event_claim_firewall():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "validation"
        / "V05C_EVENT_GATED_CLAIM_GATE.md"
    ).read_text(encoding="utf-8")

    assert "Status: **FROZEN BEFORE v0.5c OUTCOME**" in text
    assert "beta_partner = +0.75" in text
    assert "beta_partner = 0.0" in text
    assert "true event probability = **0.25**" in text
    assert "true event probability = **0.005**" in text
    assert "event effort = **0.5**" in text
    assert "event detection = **0.9**" in text
    assert "lower 90% posterior bound(P(event)) > 0.05" in text
    assert "replicates per world = **16**" in text
    assert "total fits = **32**" in text
    assert "base seed = **20261009**" in text
    assert "seed stride = **83**" in text
    assert "hidden-null offset = **1000000**" in text
    assert "warmup = **300**" in text
    assert "posterior samples = **350**" in text
    assert "chains = **2**" in text
    assert "REALIZED claim rate >= **0.75**" in text
    assert "REALIZED claim rate <= **0.25**" in text
    assert "mean fitted event probability <= **0.05**" in text
    assert "no hidden-null beta-refusal criterion" in text.lower()
    assert "total divergences / 32 <= **0.10**" in text
