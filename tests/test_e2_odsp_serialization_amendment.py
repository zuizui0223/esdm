from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / "docs" / "replication" / "E2_ODSP_SERIALIZATION_AMENDMENT_V1.json"


def _read():
    return json.loads(AMENDMENT.read_text(encoding="utf-8"))


def test_e2_odsp_amendment_preserves_current_mica_state():
    amendment = _read()
    state = amendment["scientific_state_preservation"]

    assert amendment["status"] == "FROZEN_PRE_TEMPORAL_RESPONSE"
    assert amendment["response_blind_result_merge_sha"] == (
        "7f36f41c21b06dc95995726a4576da70f4e3b5e0"
    )
    assert state["selected_candidate"] == "MICA_MUSKRAT"
    assert state["candidate_selection_status"] == "FROZEN_RESPONSE_BLIND"
    assert state["response_blind_geometry_header_status"] == (
        "RESPONSE_BLIND_GEOMETRY_HEADER_PASS"
    )
    assert state["temporal_integrity_opening"] is False
    assert state["full_ecological_response_opening"] is False
    assert state["model_fitting"] is False
    assert state["modifies_r5b_model"] is False
    assert state["modifies_e2_geometry"] is False
    assert state["modifies_e2_temporal_rule"] is False


def test_e2_odsp_amendment_requires_absolute_scores_and_deployment_rows():
    amendment = _read()
    serialization = amendment["heldout_score_serialization"]

    assert serialization["required_absolute_fields"] == [
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    ]
    assert serialization["gain_only_serialization_allowed"] is False
    assert serialization["reconstruct_absolute_scores_from_gain_allowed"] is False
    assert serialization["same_heldout_observations_across_all_three_fits"] is True

    rows = serialization["row_level_odsp_table"]
    assert rows["required"] is True
    assert rows["row_unit"] == "one east-heldout deployment"
    assert rows["row_id"] == "deploymentID"
    assert rows["minimum_group_count"] == 12
    assert rows["population_cluster"] is None
    assert rows["same_state_block_context_cells_across_all_three_fits"] is True
    assert rows["zero_count_cells_retained"] is True


def test_e2_odsp_amendment_keeps_activity_and_state_parallel():
    export = _read()["odsp_downstream_export"]

    assert export["activity_and_state_are_parallel_not_ordered"] is True
    assert export["global_information_ladder_authorized"] is False
    assert export["activity_contrast"] == {
        "lower_information": ["suitability", "state"],
        "upper_information": ["suitability", "state", "activity"],
        "lower_score_field": "activity_knockout_heldout_log_score",
        "upper_score_field": "full_heldout_log_score",
    }
    assert export["state_contrast"] == {
        "lower_information": ["suitability", "activity"],
        "upper_information": ["suitability", "activity", "state"],
        "lower_score_field": "state_knockout_heldout_log_score",
        "upper_score_field": "full_heldout_log_score",
    }


def test_e2_odsp_amendment_does_not_authorize_eog_or_n4():
    export = _read()["odsp_downstream_export"]
    auth = _read()["current_authorization"]

    assert export["downstream_population_audit_role"] == "descriptive_only"
    assert export["eog_consumption_authorized"] is False
    assert export["n4_action_authorized"] is False
    assert export["aggregate_only_export_allowed"] is False
    assert export["requires_row_level_score_table"] is True

    assert auth["temporal_integrity_opening"] is False
    assert auth["full_ecological_response_opening"] is False
    assert auth["model_fitting"] is False
    assert auth["odsp_export_execution"] is False


def test_e2_odsp_amendment_prevents_post_response_redefinition():
    governance = _read()["one_open_governance"]

    assert governance["temporal_integrity_must_pass_before_full_response_fit"] is True
    assert governance["response_conditioned_retuning_allowed"] is False
    assert governance["post_response_score_field_changes_allowed"] is False
    assert governance["post_response_odsp_information_order_changes_allowed"] is False
    assert governance["post_response_row_grouping_changes_allowed"] is False
    assert governance["replacement_candidate_after_full_response_consumption_allowed"] is False
    assert governance["failure_remains_failure"] is True
