from __future__ import annotations

from scripts.build_odsp_information_axis_capability import build


def _by_axis():
    result = build()
    return result, {row["axis_id"]: row for row in result["axes"]}


def test_capability_matrix_has_four_validated_numeric_axes():
    result, axes = _by_axis()

    assert result["validated_numeric_axis_count"] == 4
    assert result["nonvalidated_axis_count"] == 3
    assert set(axes) == {
        "accessibility",
        "dynamic_occupancy",
        "activity",
        "latent_state",
        "interaction",
        "traits",
        "movement_kernel",
    }

    for axis in ("accessibility", "dynamic_occupancy", "activity", "latent_state"):
        assert axes[axis]["capability_class"] == "validated_transfer_value"
        assert axes[axis]["numeric_transfer_value_authorized"] is True
        assert axes[axis]["population_status"] == "positive"
        assert axes[axis]["conservative_mean_value"] > 0


def test_validated_axis_values_match_frozen_portfolio():
    _, axes = _by_axis()

    assert axes["accessibility"]["population_mean_gain"] == 0.36244191577864204
    assert axes["dynamic_occupancy"]["population_mean_gain"] == 7.090827989764035
    assert axes["activity"]["population_mean_gain"] == 0.00699856015906225
    assert axes["latent_state"]["population_mean_gain"] == 0.02896466849576273

    assert axes["activity"]["ordering_relation"] == "parallel_nonordered"
    assert axes["latent_state"]["ordering_relation"] == "parallel_nonordered"
    assert axes["activity"]["parallel_family"] == "v04_r5b_activity_state"
    assert axes["latent_state"]["parallel_family"] == "v04_r5b_activity_state"


def test_interaction_failure_remains_visible_and_is_not_converted_to_zero():
    _, axes = _by_axis()
    interaction = axes["interaction"]

    assert interaction["capability_class"] == "not_authorized_numeric_transfer"
    assert interaction["numeric_transfer_value"] is None
    assert interaction["numeric_transfer_value_authorized"] is False
    assert interaction["unsupported_not_zero"] is True

    sentinel = interaction["failure_sentinel"]
    assert sentinel["source_id"] == "v05f_directed_interaction_replication"
    assert sentinel["frozen_result_status"] == "FAIL"
    assert sentinel["numeric_transfer_value"] is None
    assert sentinel["numeric_transfer_value_authorized"] is False
    assert sentinel["unsupported_not_zero"] is True
    assert sentinel["positive_world"]["positive_gain_rate"] == 1
    assert sentinel["specificity_null"]["material_gain_count"] == 5
    assert sentinel["specificity_null"]["maximum_allowed_count"] == 4


def test_traits_and_movement_kernel_are_explicit_capability_gaps():
    _, axes = _by_axis()

    traits = axes["traits"]
    movement = axes["movement_kernel"]

    assert traits["capability_class"] == "not_instrumented_no_heldout_score"
    assert traits["source_ids"] == []
    assert traits["numeric_transfer_value"] is None
    assert traits["numeric_transfer_value_authorized"] is False

    assert movement["capability_class"] == "not_instrumented_outside_current_model"
    assert movement["source_ids"] == []
    assert movement["numeric_transfer_value"] is None
    assert movement["numeric_transfer_value_authorized"] is False


def test_capability_matrix_does_not_relabel_accessibility_or_dynamics_as_movement():
    result, _ = _by_axis()
    distinctions = result["distinctions"]

    assert distinctions["accessibility_is_movement_kernel"] is False
    assert distinctions["dynamic_occupancy_is_movement_kernel"] is False
    assert distinctions["latent_state_is_trait"] is False
    assert distinctions["evidence_design_comparison_is_information_transfer"] is False
    assert distinctions["model_representation_comparison_is_information_transfer"] is False


def test_existing_sources_cannot_be_retrofitted_into_empirical_lattice():
    result, _ = _by_axis()
    lattice = result["lattice_boundary"]

    assert lattice["current_protocol_supports_block_counts"] == [2, 3]
    assert lattice["existing_activity_state_parallel_family_is_complete_lattice"] is False
    assert "suitability-only" in lattice["reason_activity_state_not_complete"]
    assert lattice["cross_programme_lattice_allowed"] is False
    assert lattice["retrospective_missing_node_reconstruction_allowed"] is False
    assert lattice["synthetic_lattice_smoke_is_scientific_result"] is False


def test_next_axis_requires_prospective_absolute_scores():
    result, _ = _by_axis()
    rule = result["next_build_rule"]

    assert rule["new_axis_requires_absolute_heldout_scores"] is True
    assert rule["same_heldout_rows_required"] is True
    assert rule["same_proper_score_required"] is True
    assert rule["strict_nested_information_required_for_chain"] is True
    assert rule["complete_subset_scores_required_for_unordered_lattice"] is True
    assert rule["outcome_access_before_axis_definition_allowed"] is False


def test_capability_matrix_does_not_authorize_downstream_action():
    result, _ = _by_axis()
    boundary = result["action_boundary"]

    assert boundary["authorizes_new_scientific_result"] is False
    assert boundary["authorizes_new_fit"] is False
    assert boundary["authorizes_rerun"] is False
    assert boundary["authorizes_eog_consumption"] is False
    assert boundary["authorizes_n4_action"] is False

    assert len(result["fingerprint"]) == 64



def test_matrix_itself_accounts_for_all_fourteen_registry_sources():
    result, axes = _by_axis()

    coverage = result["evidence_coverage"]
    assert coverage["registry_source_count"] == 14
    assert coverage["matrix_registry_source_count"] == 14
    assert coverage["matrix_every_registry_source_accounted_for"] is True
    assert coverage["non_axis_exclusion_count"] == 6

    rows = {row["source_id"]: row for row in result["non_axis_exclusions"]}
    assert set(rows) == {
        "v06b_joint_accessibility_identification",
        "v06c_budget_matched_accessibility",
        "v07a_dynamic_occupancy_identification",
        "v07c_static_vs_dynamic_occupancy",
        "v07d_equal_dimension_static_vs_dynamic",
        "v07e_reciprocal_static_world",
    }

    assert rows["v06b_joint_accessibility_identification"]["registry_status"] == (
        "identification_only_not_transfer"
    )
    assert rows["v07a_dynamic_occupancy_identification"]["registry_status"] == (
        "identification_only_not_transfer"
    )
    for source_id in (
        "v06c_budget_matched_accessibility",
        "v07c_static_vs_dynamic_occupancy",
        "v07d_equal_dimension_static_vs_dynamic",
        "v07e_reciprocal_static_world",
    ):
        assert rows[source_id]["registry_status"] == (
            "non_nested_comparison_not_transfer"
        )
        assert rows[source_id]["numeric_transfer_value"] is None
        assert rows[source_id]["numeric_transfer_value_authorized"] is False
