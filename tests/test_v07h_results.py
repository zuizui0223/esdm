import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07H_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07h_frozen_result_passes_expected_count_matched_gate():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 13
    assert payload["gate"]["checks_total"] == 13

    summary = payload["summary"]
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["selected_lower_worst_sd_rate"] == 1.0
    assert summary["mean_worst_sd_ratio"] < 0.78
    assert summary["maximum_worst_sd_ratio"] < 0.99
    assert summary["total_divergences"] == 0


def test_v07h_expected_count_matching_and_effort_saving_are_frozen():
    payload = _payload()
    control = payload["deterministic_control"]

    assert control["expected_count_relative_error"] < 1e-12
    assert abs(
        control["expected_direct_count_baseline"]
        - control["expected_direct_count_selected"]
    ) < 1e-10
    assert control["selected_to_baseline_effort_ratio"] < 0.74


def test_v07h_prediction_is_not_promoted():
    payload = _payload()

    assert payload["summary"]["positive_heldout_gain_rate"] == 0.375
    assert abs(payload["summary"]["mean_heldout_gain"]) < 0.02
    assert (
        payload["interpretation_boundary"]["predictive_superiority_established"]
        is False
    )


def test_v07h_result_provenance_is_frozen():
    payload = _payload()

    assert payload["outcome_run_id"] == 36106813627
    assert payload["outcome_head_sha"] == (
        "afee7e94f84940305f7401c844f196faebd4e760"
    )
    assert payload["result_artifact"]["github_digest"] == (
        "sha256:f3c21a0edb16f5126b1684fa00d608da372e7d84918cf200c1891b6e89740a1e"
    )
