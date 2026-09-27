from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "E2_EMPIRICAL_REPLICATION_CONTRACT_DRAFT.json"


def _read() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_e2_contract_remains_draft_and_authorizes_no_response_opening():
    contract = _read()

    assert contract["status"] == "DRAFT_NOT_AUTHORIZED"
    assert contract["relationship_to_active_programme"]["rescue_of_first_endpoint"] is False
    assert contract["relationship_to_active_programme"]["modifies_first_endpoint"] is False

    authorization = contract["current_authorization"]
    assert authorization["candidate_search"] is True
    assert authorization["candidate_selected"] is False
    assert authorization["temporal_integrity_opening"] is False
    assert authorization["full_ecological_response_opening"] is False
    assert authorization["model_fitting"] is False


def test_e2_freezes_absolute_scores_not_gain_only_outputs():
    contract = _read()
    serialization = contract["frozen_fit_and_endpoints"]["heldout_score_serialization"]

    assert serialization["required_absolute_fields"] == [
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    ]
    assert serialization["derived_gain_fields"] == {
        "activity_gain": (
            "full_heldout_log_score - activity_knockout_heldout_log_score"
        ),
        "state_gain": "full_heldout_log_score - state_knockout_heldout_log_score",
    }
    assert serialization["same_heldout_observations_across_all_three_fits"] is True
    assert serialization["gain_only_serialization_allowed"] is False
    assert serialization["reconstruct_absolute_scores_from_gain_allowed"] is False

    score = serialization["score_contract"]
    assert score["kind"] == "log"
    assert score["name"] == "mean_heldout_log_predictive_density"
    assert score["orientation"] == "higher_is_better"
    assert score["common_scoring_rule"] is True
    assert score["common_reference_measure"] is True
    assert score["unit"] == "nats_per_east_heldout_state_block_context"


def test_e2_odsp_export_keeps_activity_and_state_parallel_not_ordered():
    export = _read()["odsp_downstream_export"]

    assert export["status"] == "PROSPECTIVE_SERIALIZATION_ONLY"
    assert export["changes_e2_scientific_decision"] is False
    assert export["export_requires_completed_full_response_fit"] is True
    assert export["export_requires_finite_absolute_scores"] is True
    assert export["export_requires_same_heldout_observations"] is True

    activity = export["activity_contrast"]
    state = export["state_contrast"]

    assert activity == {
        "lower_information": ["suitability", "state"],
        "upper_information": ["suitability", "state", "activity"],
        "lower_score_field": "activity_knockout_heldout_log_score",
        "upper_score_field": "full_heldout_log_score",
    }
    assert state == {
        "lower_information": ["suitability", "activity"],
        "upper_information": ["suitability", "activity", "state"],
        "lower_score_field": "state_knockout_heldout_log_score",
        "upper_score_field": "full_heldout_log_score",
    }

    assert export["activity_and_state_are_parallel_not_ordered"] is True
    assert export["global_information_ladder_authorized"] is False
    assert export["downstream_population_audit_role"] == "descriptive_only"
    assert export["eog_consumption_authorized"] is False
    assert export["n4_action_authorized"] is False


def test_e2_post_response_cannot_change_odsp_score_contract_or_order():
    governance = _read()["one_open_governance"]

    assert governance["response_conditioned_retuning_allowed"] is False
    assert governance["post_response_score_field_changes_allowed"] is False
    assert governance["post_response_odsp_information_order_changes_allowed"] is False
    assert governance["replacement_candidate_after_full_response_consumption_allowed"] is False
    assert governance["failure_remains_failure"] is True


def test_e2_freezes_deployment_level_score_rows_for_future_population_audit():
    contract = _read()
    serialization = contract["frozen_fit_and_endpoints"]["heldout_score_serialization"]
    rows = serialization["row_level_odsp_table"]

    assert rows["required"] is True
    assert rows["row_unit"] == "one east-heldout deployment"
    assert rows["row_id"] == "deploymentID"
    assert rows["group_semantics"] == "east-heldout camera deployment"
    assert rows["minimum_group_count"] == 12
    assert rows["weight"] == "1.0 per deployment"
    assert rows["population_cluster"] is None
    assert rows["required_columns"] == [
        "deploymentID",
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    ]
    assert rows["same_state_block_context_cells_across_all_three_fits"] is True
    assert rows["zero_count_cells_retained"] is True
    assert rows["post_response_row_grouping_changes_allowed"] is False
    assert rows["post_response_score_aggregation_changes_allowed"] is False

    consistency = serialization["aggregate_consistency"]
    assert consistency["equal_weight_mean_of_deployment_rows_must_equal_aggregate_score"] is True
    assert consistency["absolute_tolerance"] == 1e-12
    assert consistency["required_for"] == [
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    ]


def test_e2_odsp_population_audit_requires_row_level_scores_not_aggregate_only():
    export = _read()["odsp_downstream_export"]

    assert export["group_semantics"] == "east-heldout camera deployment"
    assert export["minimum_population_group_count"] == 12
    assert export["population_cluster"] is None
    assert export["aggregate_only_export_allowed"] is False
    assert export["requires_row_level_score_table"] is True
    assert "descriptive population-of-heldout-deployments audit" in (
        export["population_inference_role"]
    )
