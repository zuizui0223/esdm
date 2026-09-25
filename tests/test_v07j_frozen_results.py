from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs" / "validation" / "V07J_FROZEN_RESULTS.json"
INVALID = ROOT / "docs" / "validation" / "V07J_INVALIDATED_RUN_36117506781.json"


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_v07j_frozen_result_uses_replacement_run_not_invalidated_run():
    result = _read(RESULT)
    invalid = _read(INVALID)

    assert result["status"] == "PASS"
    assert result["outcome_run_id"] == 36118096281
    assert result["outcome_head_sha"] == "e68990272bbe00a65b2e60bc80eabbc48fb290ec"
    assert result["replacement_authorization"] == "r1"
    assert result["invalidated_predecessor_run_id"] == 36117506781

    assert invalid["invalidated_run"]["workflow_run_id"] == 36117506781
    assert invalid["invalidated_run"]["scientific_outcome_generated"] is False
    assert invalid["failure_class"] == "implementation_infrastructure_bug"
    assert invalid["repair"]["scientific_gate_changed"] is False


def test_v07j_all_three_shift_worlds_pass_precision_transfer():
    result = _read(RESULT)
    summary = result["summary"]
    worlds = summary["world_summaries"]

    assert summary["total_replicates"] == 36
    assert summary["total_fit_count"] == 72
    assert summary["total_divergences"] == 0
    assert summary["pooled_selected_lower_worst_sd_rate"] == 35 / 36
    assert summary["pooled_mean_worst_sd_ratio"] == 0.7991896040628926

    assert worlds["low_occupancy"]["selected_lower_worst_sd_rate"] == 1.0
    assert worlds["low_occupancy"]["mean_worst_sd_ratio"] == 0.8050227851366554

    assert worlds["high_occupancy"]["selected_lower_worst_sd_rate"] == 11 / 12
    assert worlds["high_occupancy"]["mean_worst_sd_ratio"] == 0.7261308065846589

    assert worlds["high_turnover"]["selected_lower_worst_sd_rate"] == 1.0
    assert worlds["high_turnover"]["mean_worst_sd_ratio"] == 0.8664152204673635


def test_v07j_recovery_guardrails_pass_in_every_shift_world():
    worlds = _read(RESULT)["summary"]["world_summaries"]

    for world in worlds.values():
        assert all(abs(value) <= 0.20 for value in world["selected_mean_biases"].values())
        assert all(value >= 2 / 3 for value in world["selected_coverages"].values())


def test_v07j_prediction_remains_descriptive_and_small():
    worlds = _read(RESULT)["summary"]["world_summaries"]

    assert worlds["low_occupancy"]["mean_heldout_gain"] == 0.01819024635504936
    assert worlds["high_occupancy"]["mean_heldout_gain"] == 0.004494779429101407
    assert worlds["high_turnover"]["mean_heldout_gain"] == 0.01995218596465313
    assert any(world["minimum_heldout_gain"] < 0 for world in worlds.values())


def test_v07j_result_is_not_odsp_information_transfer():
    result = _read(RESULT)
    boundary = result["interpretation_boundary"]

    assert result["gate"] == {
        "passed": True,
        "checks_passed": 36,
        "checks_total": 36,
    }
    assert boundary["pilot_selected_schedule_transfer_across_frozen_population_shifts"] is True
    assert boundary["universal_population_shift_robustness"] is False
    assert boundary["predictive_superiority_established"] is False
    assert boundary["odsp_information_transfer_source"] is False
    assert boundary["movement_or_connectivity"] is False
    assert boundary["empirical_biological_validity"] is False


def test_v07j_artifact_provenance_is_pinned():
    artifact = _read(RESULT)["result_artifact"]

    assert artifact["id"] == 10855703479
    assert artifact["github_digest"] == (
        "sha256:aae71e79c77061fe074292a53f0e01e4be26c34776014ffcf05a365795881960"
    )
    assert artifact["result_json_sha256"] == (
        "10baa9eaded4c3c07d79cc02a97f917b12ce668214d79bf5fcea4b3b56036330"
    )
