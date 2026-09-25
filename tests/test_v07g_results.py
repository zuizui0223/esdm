import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07G_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07g_frozen_result_passes_precision_gate():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 13
    assert payload["gate"]["checks_total"] == 13

    summary = payload["summary"]
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["optimized_lower_worst_sd_rate"] == 1.0
    assert summary["mean_worst_sd_ratio"] < 0.68
    assert summary["maximum_worst_sd_ratio"] < 0.82
    assert summary["total_divergences"] == 0


def test_v07g_prediction_remains_descriptive_not_promoted():
    payload = _payload()
    summary = payload["summary"]

    assert summary["positive_heldout_gain_rate"] == 0.5625
    assert abs(summary["mean_heldout_gain"]) < 0.05
    assert payload["interpretation_boundary"]["predictive_superiority_established"] is False


def test_v07g_provenance_and_design_selection_are_frozen():
    payload = _payload()

    assert payload["outcome_run_id"] == 36105638747
    assert payload["outcome_head_sha"] == (
        "c033585d0a4fe958675d7c9f838be1532551785f"
    )
    assert payload["selection"]["selected_placement"] == [2, 6, 7, 8]
    assert payload["selection"]["baseline_placement"] == [1, 2, 3, 4]
    assert payload["result_artifact"]["github_digest"] == (
        "sha256:d3e736de84b62b399f3b61e1b22755069b0236e99616acf4680ae6dbcdb78bbf"
    )
