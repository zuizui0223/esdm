from __future__ import annotations

import pytest

from esdm.domain import Context, ExplicitGrid


def test_explicit_grid_preserves_declared_context_order_and_axes():
    keys = (
        ("b", 8, 9),
        ("a", 1, 3),
        ("b", 1, 3),
    )
    grid = ExplicitGrid(keys)

    assert grid.keys == keys
    assert tuple(grid.contexts()) == (
        Context("b", 8, 9),
        Context("a", 1, 3),
        Context("b", 1, 3),
    )
    assert grid.space == ("b", "a")
    assert grid.doy == (8, 1)
    assert grid.hour == (9, 3)


def test_explicit_grid_rejects_duplicate_or_invalid_contexts():
    with pytest.raises(ValueError, match="unique"):
        ExplicitGrid((("a", 1, 3), ("a", 1, 3)))
    with pytest.raises(ValueError, match="doy"):
        ExplicitGrid((("a", 0, 3),))
    with pytest.raises(ValueError, match="hour"):
        ExplicitGrid((("a", 1, 24),))
