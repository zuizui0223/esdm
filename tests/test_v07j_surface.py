from itertools import product

from esdm.validate.v07j_surface import (
    V07J_EPSILON_GRID,
    V07J_GAMMA_GRID,
    V07J_PSI0_GRID,
)


def test_v07j_grid_is_frozen_to_thirty_six_population_shift_cells():
    cells = tuple(product(V07J_PSI0_GRID, V07J_GAMMA_GRID, V07J_EPSILON_GRID))

    assert len(cells) == 36
    assert (0.20, 0.35, 0.15) in cells
    assert V07J_PSI0_GRID == (0.10, 0.20, 0.50, 0.80)
    assert V07J_GAMMA_GRID == (0.15, 0.35, 0.55)
    assert V07J_EPSILON_GRID == (0.05, 0.15, 0.30)
