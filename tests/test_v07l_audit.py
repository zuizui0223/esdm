from __future__ import annotations

from esdm.validate.v07l_audit import (
    V07L_EPSILON_GRID,
    V07L_GAMMA_GRID,
    V07L_PSI0_GRID,
    V07L_TRIGGER_RATIO,
    evaluate_v07l_audit,
    evaluate_v07l_candidate_surface,
    select_v07l_confirmatory_worlds,
)


def test_v07l_fresh_grid_is_exactly_36_new_shift_cells():
    cells = evaluate_v07l_candidate_surface()

    assert V07L_TRIGGER_RATIO == 0.80
    assert V07L_PSI0_GRID == (0.15, 0.35, 0.65, 0.85)
    assert V07L_GAMMA_GRID == (0.25, 0.45, 0.65)
    assert V07L_EPSILON_GRID == (0.08, 0.22, 0.38)
    assert len(cells) == 36
    assert len({row.cell_id for row in cells}) == 36

    prior_worlds = {
        (0.10, 0.20, 0.30),
        (0.50, 0.55, 0.10),
        (0.20, 0.55, 0.40),
        (0.20, 0.15, 0.05),
        (0.80, 0.15, 0.30),
    }
    assert all(
        (row.psi0, row.gamma, row.epsilon) not in prior_worlds
        for row in cells
    )


def test_v07l_selected_world_roles_are_unique_and_straddle_trigger():
    cells = evaluate_v07l_candidate_surface()
    selected = select_v07l_confirmatory_worlds(cells)

    assert set(selected) == {
        "strong_headroom",
        "threshold_below",
        "threshold_above",
        "negligible_headroom",
    }
    assert len({row.cell_id for row in selected.values()}) == 4

    assert (
        selected["strong_headroom"].local_oracle_to_transferred_ratio
        <= V07L_TRIGGER_RATIO
    )
    assert (
        selected["threshold_below"].local_oracle_to_transferred_ratio
        <= V07L_TRIGGER_RATIO
    )
    assert (
        selected["threshold_above"].local_oracle_to_transferred_ratio
        > V07L_TRIGGER_RATIO
    )
    assert (
        selected["negligible_headroom"].local_oracle_to_transferred_ratio
        > V07L_TRIGGER_RATIO
    )


def test_v07l_role_selection_matches_frozen_deterministic_rules():
    cells = evaluate_v07l_candidate_surface()
    selected = select_v07l_confirmatory_worlds(cells)
    eligible = tuple(row for row in cells if row.eligible)

    below = [
        row
        for row in eligible
        if row.local_oracle_to_transferred_ratio <= V07L_TRIGGER_RATIO
    ]
    above = [
        row
        for row in eligible
        if row.local_oracle_to_transferred_ratio > V07L_TRIGGER_RATIO
    ]

    assert selected["strong_headroom"].local_oracle_to_transferred_ratio == min(
        row.local_oracle_to_transferred_ratio for row in below
    )

    remaining_below = [
        row for row in below
        if row.cell_id != selected["strong_headroom"].cell_id
    ]
    assert (
        V07L_TRIGGER_RATIO
        - selected["threshold_below"].local_oracle_to_transferred_ratio
        == min(
            V07L_TRIGGER_RATIO - row.local_oracle_to_transferred_ratio
            for row in remaining_below
        )
    )

    assert (
        selected["threshold_above"].local_oracle_to_transferred_ratio
        - V07L_TRIGGER_RATIO
        == min(
            row.local_oracle_to_transferred_ratio - V07L_TRIGGER_RATIO
            for row in above
        )
    )

    remaining_above = [
        row for row in above
        if row.cell_id != selected["threshold_above"].cell_id
    ]
    assert (
        selected["negligible_headroom"].local_oracle_to_transferred_ratio
        == max(row.local_oracle_to_transferred_ratio for row in remaining_above)
    )


def test_v07l_all_selected_worlds_keep_transferred_schedule_estimable():
    audit = evaluate_v07l_audit()

    assert audit.trigger_ratio == 0.80
    assert all(row.eligible for row in audit.selected_worlds.values())
    assert all(
        row.transferred_structural_pass
        and row.transferred_conditioning_pass
        for row in audit.selected_worlds.values()
    )
