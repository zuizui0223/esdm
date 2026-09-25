import json
from pathlib import Path


def _payload():
    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "docs" / "validation" / "V07I_FROZEN_RESULTS.json"
        ).read_text(encoding="utf-8")
    )


def test_v07i_frozen_result_passes_burned_pilot_gate():
    payload = _payload()

    assert payload["status"] == "PASS"
    assert payload["gate"]["passed"] is True
    assert payload["gate"]["checks_passed"] == 13
    assert payload["gate"]["checks_total"] == 13

    summary = payload["summary"]
    assert summary["replicates"] == 16
    assert summary["fit_count"] == 48
    assert summary["selected_lower_worst_sd_rate"] == 1.0
    assert summary["mean_worst_sd_ratio"] < 0.67
    assert summary["oracle_placement_selection_rate"] == 1.0
    assert summary["selection_counts"] == {"2,6,7,8": 16}
    assert summary["total_divergences"] == 0


def test_v07i_provenance_and_disjoint_selection_boundary_are_frozen():
    payload = _payload()

    assert payload["outcome_run_id"] == 36110445348
    assert payload["outcome_head_sha"] == (
        "a02da1065d7699e68c18a13aea324a52cd65b319"
    )
    assert payload["gate_freeze_commit"] == (
        "aa3ac6917b9e990c6da9f0cf3e5ae7efcb281e4e"
    )
    assert payload["gate_blob_sha"] == (
        "c6679964dbc62d08ad3dcf925d271f7a6c625353"
    )
    assert payload["result_artifact"]["github_digest"] == (
        "sha256:78c9b5fb6cb87351c8a7925d505dc5b8a8e96a4337965fbfb96c01961d22b368"
    )

    boundary = payload["interpretation_boundary"]
    assert boundary["pilot_and_confirmatory_seed_families_disjoint"] is True
    assert boundary["selector_uses_generating_truth"] is False
    assert boundary["confirmatory_data_used_for_selection"] is False
    assert boundary["pilot_adaptive_calibration_placement_established"] is True
    assert boundary["population_shift_robustness"] is False
