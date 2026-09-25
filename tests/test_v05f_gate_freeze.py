from pathlib import Path


def test_v05f_gate_inherits_v05a_science_and_adds_only_serialization():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V05F_INTERACTION_TRANSFER_REPLICATION_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE v0.5f IDENTIFICATION OR MCMC OUTCOME" in text
    assert "independent-seed replication" in text
    assert "beta_partner = +0.75" in text
    assert "beta_partner = 0.0" in text
    assert "36 spatial contexts" in text
    assert "24 training spaces" in text
    assert "12 held-out spaces" in text
    assert "16 replicates per world" in text
    assert "total fits = 64" in text
    assert "warmup = 300" in text
    assert "posterior samples = 350" in text
    assert "base seed = 20271001" in text
    assert "seed stride = 73" in text
    assert "abs(mean beta bias) <= 0.15" in text
    assert "mean Full-minus-knockout held-out gain >= 0.005" in text
    assert "abs(mean fitted beta) <= 0.10" in text
    assert "mean Full-minus-knockout held-out gain <= 0.005" in text
    assert "full_heldout_log_score" in text
    assert "partner_knockout_heldout_log_score" in text
    assert "No synthetic zero baseline" in text
    assert "measured_environment + directed_partner_latent" in text
