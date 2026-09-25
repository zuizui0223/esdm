from pathlib import Path


def test_v07k_gate_document_freezes_local_repilot_programme():
    text = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07K_LOCAL_REPILOT_GATE.md"
    ).read_text(encoding="utf-8")

    assert "FROZEN AFTER DETERMINISTIC AUDIT, BEFORE CONFIRMATORY MCMC OUTCOME" in text
    assert "incremental local-adaptation hypothesis" in text
    assert "already shown robust precision transfer" in text
    assert "35/36 paired replicates" in text
    assert "not the three v0.7j confirmatory target populations" in text
    assert "local oracle placement: (1,3,7,8)" in text
    assert "local oracle placement: (1,2,7,8)" in text
    assert "pilot base seed = 20261321" in text
    assert "confirmatory base seed = 20261421" in text
    assert "pilot base seed = 20271321" in text
    assert "confirmatory base seed = 20271421" in text
    assert "seed stride = 181" in text
    assert "total fits = 96" in text
    assert "rate >= 0.75" in text
    assert "mean adaptive/transferred ratio <= 0.95" in text
    assert "divergences / fit <= 0.10" in text
