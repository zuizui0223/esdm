import json
from pathlib import Path


def _result():
    path = (
        Path(__file__).resolve().parents[1]
        / "docs" / "validation" / "V07C_FROZEN_RESULTS.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_v07c_frozen_result_is_pass_and_matches_authorized_run():
    result = _result()

    assert result["status"] == "PASS"
    assert result["outcome_run_id"] == 36078426459
    assert result["outcome_head_sha"] == (
        "08a3fca65cb4fcb3ba1cdd135d92e7bde9513775"
    )
    assert result["gate_freeze_commit"] == (
        "42772573e83b85174cfad8dc5d9ba5bcd77655af"
    )
    assert result["gate_blob_sha"] == (
        "95c6e8b7d77a7164574e7afd013dc47fbfbdcb4a"
    )


def test_v07c_frozen_result_passes_matched_predictive_gate():
    result = _result()
    summary = result["summary"]

    assert summary["replicates"] == 16
    assert summary["fit_count"] == 32
    assert summary["dynamic_better_count"] == 15
    assert summary["dynamic_better_rate"] == 0.9375
    assert summary["mean_dynamic_gain"] == 3.3212365823630834
    assert summary["minimum_dynamic_gain"] == -0.1168403622198042
    assert summary["total_divergences"] == 0
    assert result["gate"]["passed"] is True


def test_v07c_static_comparator_was_estimable():
    result = _result()
    qualification = result["qualification"]

    assert qualification["static_structural_pass"] is True
    assert qualification["static_practical_pass"] is True
    assert qualification["static_rank"] == qualification["static_parameter_count"] == 3
    assert qualification["static_condition_number"] < 1000.0
    assert all(
        value <= 0.25
        for value in qualification["static_target_sd_proxies"].values()
    )


def test_v07c_boundary_does_not_promote_movement_or_empirical_claims():
    boundary = _result()["interpretation_boundary"]

    assert (
        boundary[
            "recursive_dynamics_outperform_matched_memoryless_occupancy_in_frozen_world"
        ]
        is True
    )
    assert boundary["universal_dynamic_superiority"] is False
    assert boundary["realized_binary_occupancy_history_established"] is False
    assert boundary["colonization_extinction_events_observed"] is False
    assert boundary["movement_kernel_identified"] is False
    assert boundary["connectivity_identified"] is False
    assert boundary["source_sink_dynamics_identified"] is False
    assert boundary["causal_movement_limitation"] is False
    assert boundary["empirical_biological_validity"] is False
