import importlib.util

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, OccupiedPresenceOnly
from esdm.process import LinearSuitability, StaticLinearOccupancy


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _grid():
    return Grid(space=("a",), doy=(1, 2, 3, 4), hour=(0,))


def _covariates(grid):
    times = (-1.0, -0.25, 0.5, 1.0)
    return {
        key: {
            "time": times[index],
            "time2": times[index] * times[index],
        }
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
                    covariates=("time", "time2"),
                    intercept_parameter="occupancy_intercept",
                    coefficient_parameters={
                        "time": "beta_time",
                        "time2": "beta_time2",
                    },
                ),
            )
        },
        (stream,),
    )


def _theta():
    return {
        "sp": {
            "alpha": 0.2,
            "occupancy_intercept": -0.5,
            "beta_time": 1.5,
            "beta_time2": 0.25,
        }
    }


def test_quadratic_static_occupancy_is_memoryless_and_bounded():
    grid = _grid()
    covariates = _covariates(grid)
    fields = _model(grid).latent_fields(_theta(), covariates)

    values = [fields.occupancy["sp"][key] for key in grid.keys]
    assert all(0.0 < value < 1.0 for value in values)

    changed = {key: dict(values) for key, values in covariates.items()}
    changed[grid.keys[0]]["time"] = 10.0
    changed[grid.keys[0]]["time2"] = 100.0
    changed_fields = _model(grid).latent_fields(_theta(), changed)

    assert changed_fields.occupancy["sp"][grid.keys[1]] == pytest.approx(
        fields.occupancy["sp"][grid.keys[1]]
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_quadratic_static_occupancy_scalar_and_array_paths_match():
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
