import importlib.util

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, OccupiedPresenceOnly
from esdm.process import LinearSuitability, StaticLinearOccupancy


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _grid():
    return Grid(space=("a",), doy=(1, 2, 3), hour=(0,))


def _covariates(grid):
    values = (-1.0, 0.0, 1.0)
    return {
        key: {"time": values[index]}
        for index, key in enumerate(grid.keys)
    }


def _model(grid):
    stream = OccupiedPresenceOnly(
        "joint",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability", "occupancy"}),
        targets=frozenset({"sp"}),
    )
    return Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=(),
                    intercept_parameter="alpha",
                    coefficient_parameters={},
                ),
                StaticLinearOccupancy(
                    covariates=("time",),
                    intercept_parameter="occupancy_intercept",
                    coefficient_parameters={"time": "beta_time"},
                ),
            )
        },
        (stream,),
    )


def _theta():
    return {
        "sp": {
            "alpha": 0.2,
            "occupancy_intercept": 0.0,
            "beta_time": 1.0,
        }
    }


def test_static_occupancy_is_bounded_memoryless_and_has_explicit_knockout():
    grid = _grid()
    covariates = _covariates(grid)
    model = _model(grid)
    fields = model.latent_fields(_theta(), covariates)

    observed = [
        fields.occupancy["sp"][key]
        for key in grid.keys
    ]
    assert observed[0] < observed[1] < observed[2]
    assert all(0.0 < value < 1.0 for value in observed)

    knocked = model.knockout("sp", "occupancy")
    knocked_fields = knocked.latent_fields(
        {"sp": {"alpha": 0.2}},
        covariates,
    )
    assert all(
        knocked_fields.occupancy["sp"][key] == pytest.approx(1.0)
        for key in grid.keys
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_static_occupancy_scalar_and_array_paths_match():
    import jax.numpy as jnp

    grid = _grid()
    covariates = _covariates(grid)
    model = _model(grid)

    scalar = model.latent_fields(_theta(), covariates)
    array = model.latent_field_arrays(
        _theta(),
        covariates,
        array_module=jnp,
    )

    assert list(map(float, array.occupancy["sp"].values)) == pytest.approx(
        [scalar.occupancy["sp"][key] for key in grid.keys]
    )
