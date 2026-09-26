import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import DesignUninformedError, Model
from esdm.observe import EffortField, OccupiedPresenceOnly
from esdm.process import ColonizationExtinctionOccupancy, LinearSuitability


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _logit(probability: float) -> float:
    return math.log(probability / (1.0 - probability))


def _processes():
    return (
        LinearSuitability(
            covariates=(),
            intercept_parameter="alpha",
            coefficient_parameters={},
        ),
        ColonizationExtinctionOccupancy(
            initial_logit_parameter="psi0_logit",
            colonization_intercept_parameter="gamma_logit",
            extinction_intercept_parameter="epsilon_logit",
        ),
    )


def _theta(alpha: float = 0.0):
    return {
        "sp": {
            "alpha": alpha,
            "psi0_logit": _logit(0.2),
            "gamma_logit": _logit(0.5),
            "epsilon_logit": _logit(0.25),
        }
    }


def _stream(grid, *, effort: float = 1.0):
    return OccupiedPresenceOnly(
        "occupied",
        effort=EffortField({key: effort for key in grid.keys}),
        informs=frozenset({"suitability", "occupancy"}),
        targets=frozenset({"sp"}),
    )


def _model(grid, *, effort: float = 1.0):
    return Model(
        grid,
        {"sp": _processes()},
        (_stream(grid, effort=effort),),
    )


def test_colonization_extinction_recursion_matches_declared_transition():
    grid = Grid(space=("a",), doy=(1, 2, 3), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    fields = _model(grid).latent_fields(_theta(), covariates)

    assert fields.occupancy["sp"][("a", 1, 0)] == pytest.approx(0.2)
    assert fields.occupancy["sp"][("a", 2, 0)] == pytest.approx(0.55)
    assert fields.occupancy["sp"][("a", 3, 0)] == pytest.approx(0.6375)


def test_transition_covariates_act_on_destination_context():
    grid = Grid(space=("a",), doy=(1, 2), hour=(0,))
    covariates = {
        ("a", 1, 0): {"resource": 0.0, "stress": 0.0},
        ("a", 2, 0): {"resource": 1.0, "stress": -1.0},
    }
    processes = (
        LinearSuitability(
            covariates=(),
            intercept_parameter="alpha",
            coefficient_parameters={},
        ),
        ColonizationExtinctionOccupancy(
            initial_logit_parameter="psi0_logit",
            colonization_intercept_parameter="gamma_logit",
            extinction_intercept_parameter="epsilon_logit",
            colonization_covariates=("resource",),
            colonization_coefficient_parameters={"resource": "beta_resource"},
            extinction_covariates=("stress",),
            extinction_coefficient_parameters={"stress": "beta_stress"},
        ),
    )
    stream = _stream(grid)
    model = Model(grid, {"sp": processes}, (stream,))
    theta = {
        "sp": {
            "alpha": 0.0,
            "psi0_logit": _logit(0.2),
            "gamma_logit": 0.0,
            "epsilon_logit": 0.0,
            "beta_resource": math.log(3.0),
            "beta_stress": math.log(3.0),
        }
    }

    fields = model.latent_fields(theta, covariates)

    # At the destination context gamma=0.75 and epsilon=0.25.
    assert fields.occupancy["sp"][("a", 2, 0)] == pytest.approx(0.75)


def test_dynamic_occupancy_uses_chronology_not_declared_grid_order():
    grid = Grid(space=("a",), doy=(3, 1, 2), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    fields = _model(grid).latent_fields(_theta(), covariates)

    assert fields.occupancy["sp"][("a", 1, 0)] == pytest.approx(0.2)
    assert fields.occupancy["sp"][("a", 2, 0)] == pytest.approx(0.55)
    assert fields.occupancy["sp"][("a", 3, 0)] == pytest.approx(0.6375)


def test_each_space_starts_from_the_same_initial_occupancy():
    grid = Grid(space=("a", "b"), doy=(1, 2), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    fields = _model(grid).latent_fields(_theta(), covariates)

    for space in ("a", "b"):
        assert fields.occupancy["sp"][(space, 1, 0)] == pytest.approx(0.2)
        assert fields.occupancy["sp"][(space, 2, 0)] == pytest.approx(0.55)


def test_occupied_presence_multiplies_intensity_by_occupancy():
    grid = Grid(space=("a",), doy=(1, 2), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    model = _model(grid, effort=3.0)
    fields = model.latent_fields(_theta(alpha=math.log(2.0)), covariates)
    stream = model.streams[0]
    rates = stream.expected_rates("sp", fields, covariates=covariates)

    for key in grid.keys:
        expected = (
            math.exp(fields.log_intensity["sp"][key])
            * fields.occupancy["sp"][key]
            * 3.0
        )
        assert rates[key] == pytest.approx(expected)


def test_occupancy_knockout_sets_probability_to_one():
    grid = Grid(space=("a",), doy=(1, 2, 3), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    knocked = _model(grid).knockout("sp", "occupancy")
    fields = knocked.latent_fields({"sp": {"alpha": 0.0}}, covariates)

    assert all(
        fields.occupancy["sp"][key] == pytest.approx(1.0)
        for key in grid.keys
    )


def test_occupied_presence_requires_occupancy_process():
    grid = Grid(space=("a",), doy=(1, 2), hour=(0,))
    stream = _stream(grid)
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=(),
                    intercept_parameter="alpha",
                    coefficient_parameters={},
                ),
            )
        },
        (stream,),
    )

    with pytest.raises(DesignUninformedError, match="occupancy"):
        model.check_design()


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_dynamic_occupancy_scalar_and_array_fields_match():
    import jax.numpy as jnp

    grid = Grid(space=("a", "b"), doy=(3, 1, 2), hour=(0,))
    covariates = {key: {} for key in grid.keys}
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
