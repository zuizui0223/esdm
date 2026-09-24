from pathlib import Path


def test_v07b_gate_document_freezes_dynamic_recovery_transfer_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07B_DYNAMIC_RECOVERY_TRANSFER_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN BEFORE ANY v0.7b MCMC OR HELD-OUT OUTCOME" in text
    assert "training: doy 1-8" in text
    assert "future held-out scoring: doy 9-12" in text
    assert "direct OccupancyCount effort = 0 in contexts 5-12" in text
    assert "full chronological" in text
    assert "target-SD proxy <= 0.35" in text
    assert "replicates = 16" in text
    assert "total fits = 32" in text
    assert "base seed = 20261029" in text
    assert "stride = 109" in text
    assert "warmup = 300" in text
    assert "retained posterior draws = 350" in text
    assert "absolute mean posterior bias <= 0.25" in text
    assert "empirical 90% interval coverage >= 0.75" in text
    assert "Full > occupancy knockout in >= 75% of replicates" in text
    assert "mean Full-minus-knockout held-out log-score gain >= 0.005" in text
    assert "full_heldout_log_score" in text
    assert "occupancy_knockout_heldout_log_score" in text
    assert "ODSP readiness requirement" in text
