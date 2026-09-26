from __future__ import annotations

from itertools import product

from esdm.validate.v07l_audit import (
    V07LAuditCell,
    V07L_EPSILON_GRID,
    V07L_GAMMA_GRID,
    V07L_PSI0_GRID,
    V07L_TRIGGER_RATIO,
    select_v07l_confirmatory_worlds,
)


def _cell(cell_id: str, ratio: float) -> V07LAuditCell:
    return V07LAuditCell(
        cell_id=cell_id,
        psi0=0.35,
        gamma=0.45,
        epsilon=0.22,
        local_oracle_placement=(1, 2, 7, 8),
        local_oracle_worst_dynamic_sd=ratio,
        transferred_worst_dynamic_sd=1.0,
        local_oracle_to_transferred_ratio=ratio,
        transferred_structural_pass=True,
        transferred_conditioning_pass=True,
        eligible=True,
    )


def test_v07l_fresh_grid_is_exactly_36_new_shift_cells():
    assert V07L_TRIGGER_RATIO == 0.80
    assert V07L_PSI0_GRID == (0.15, 0.35, 0.65, 0.85)
    assert V07L_GAMMA_GRID == (0.25, 0.45, 0.65)
    assert V07L_EPSILON_GRID == (0.08, 0.22, 0.38)

    fresh = set(product(V07L_PSI0_GRID, V07L_GAMMA_GRID, V07L_EPSILON_GRID))
    assert len(fresh) == 36

    prior_worlds = {
        (0.10, 0.20, 0.30),
        (0.50, 0.55, 0.10),
        (0.20, 0.55, 0.40),
        (0.20, 0.15, 0.05),
        (0.80, 0.15, 0.30),
    }
    assert fresh.isdisjoint(prior_worlds)


def test_v07l_selection_roles_are_unique_and_straddle_trigger():
    cells = (
        _cell("strong", 0.55),
        _cell("below_far", 0.70),
        _cell("below_near", 0.79),
        _cell("above_near", 0.81),
        _cell("above_mid", 0.90),
        _cell("negligible", 0.99),
    )
    selected = select_v07l_confirmatory_worlds(cells)

    assert {role: row.cell_id for role, row in selected.items()} == {
        "strong_headroom": "strong",
        "threshold_below": "below_near",
        "threshold_above": "above_near",
        "negligible_headroom": "negligible",
    }


def test_v07l_selection_fails_closed_without_two_worlds_per_side():
    cells = (
        _cell("below_one", 0.70),
        _cell("above_one", 0.90),
        _cell("above_two", 0.95),
        _cell("above_three", 0.99),
    )

    import pytest

    with pytest.raises(RuntimeError, match=">=2 worlds on each side"):
        select_v07l_confirmatory_worlds(cells)


def test_v07l_selection_ignores_ineligible_cells():
    bad = V07LAuditCell(
        cell_id="ineligible",
        psi0=0.35,
        gamma=0.45,
        epsilon=0.22,
        local_oracle_placement=(1, 2, 7, 8),
        local_oracle_worst_dynamic_sd=0.10,
        transferred_worst_dynamic_sd=1.0,
        local_oracle_to_transferred_ratio=0.10,
        transferred_structural_pass=False,
        transferred_conditioning_pass=False,
        eligible=False,
    )
    cells = (
        bad,
        _cell("strong", 0.60),
        _cell("below_near", 0.79),
        _cell("above_near", 0.81),
        _cell("negligible", 0.99),
    )
    selected = select_v07l_confirmatory_worlds(cells)

    assert "ineligible" not in {row.cell_id for row in selected.values()}
