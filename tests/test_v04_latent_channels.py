import importlib.util
import math

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import DesignUninformedError, Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearActivity, LinearState, LinearSuitability


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _presence_stream(grid):
    return PresenceOnly(
        "records",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )


def test_intensity_only_model_remains_unchanged_and_has_neutral_activity():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    ("x",),
                    "intercept",
                    {"x": "beta_x"},
                ),
            )
        },
        (_presence_stream(grid),),
    )
    theta = {"sp": {"intercept": 0.1, "beta_x": 0.2}}
    covariates = {
        grid.keys[0]: {"x": -1.0},
        grid.keys[1]: {"x": 2.0},
    }

    fields = model.latent_fields(theta, covariates)

    assert tuple(fields.log_intensity["sp"].values()) == pytest.approx(
        (-0.1, 0.5)
    )
    assert tuple(fields.activity["sp"].values()) == pytest.approx((1.0, 1.0))
    assert "sp" not in fields.state_probabilities


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_scalar_and_array_latent_channels_match():
    import jax.numpy as jnp

    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    processes = (
        LinearSuitability(("x",), "intercept", {"x": "beta_x"}),
        LinearActivity(
            ("x",),
            "activity_intercept",
            {"x": "activity_beta_x"},
        ),
        LinearState(
            states,
            "resting",
            ("x",),
            {"foraging": "alpha_foraging"},
            {"foraging": {"x": "beta_foraging_x"}},
        ),
    )
    model = Model(grid, {"sp": processes}, (_presence_stream(grid),))
    theta = {
        "sp": {
            "intercept": 0.1,
            "beta_x": 0.2,
            "activity_intercept": -0.4,
            "activity_beta_x": 0.5,
            "alpha_foraging": 0.3,
            "beta_foraging_x": 0.6,
        }
    }
    covariates = {
        grid.keys[0]: {"x": -1.0},
        grid.keys[1]: {"x": 2.0},
    }

    scalar = model.latent_fields(theta, covariates)
    array = model.latent_field_arrays(theta, covariates, array_module=jnp)

    assert list(map(float, array.log_intensity["sp"].values)) == pytest.approx(
        [scalar.log_intensity["sp"][key] for key in grid.keys]
    )
    assert list(map(float, array.activity["sp"].values)) == pytest.approx(
        [scalar.activity["sp"][key] for key in grid.keys]
    )
    assert array.state_probabilities["sp"].states == ("resting", "foraging")
    for index, key in enumerate(grid.keys):
        assert list(map(float, array.state_probabilities["sp"].values[index])) == pytest.approx(
            scalar.state_probabilities["sp"][key]
        )
        assert sum(scalar.state_probabilities["sp"][key]) == pytest.approx(1.0)


def test_activity_or_state_process_without_consuming_stream_fails_closed():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability((), "intercept", {}),
                LinearActivity((), "activity_intercept", {}),
                LinearState(
                    states,
                    "resting",
                    (),
                    {"foraging": "alpha_foraging"},
                    {"foraging": {}},
                ),
            )
        },
        (
            PresenceOnly(
                "records",
                effort=EffortField({grid.keys[0]: 1.0}),
                informs=frozenset({"suitability", "activity", "state"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )

    with pytest.raises(DesignUninformedError):
        model.check_design()


def test_inconsistent_state_axes_fail_during_latent_composition():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    model = Model(
        grid,
        {
            "sp": (
                LinearState(
                    StateSpace(("resting", "foraging")),
                    "resting",
                    (),
                    {"foraging": "alpha_foraging"},
                    {"foraging": {}},
                    name="state_a",
                ),
                LinearState(
                    StateSpace(("resting", "moving")),
                    "resting",
                    (),
                    {"moving": "alpha_moving"},
                    {"moving": {}},
                    name="state_b",
                ),
            )
        },
        (_presence_stream(grid),),
    )

    with pytest.raises(ValueError, match="state.*labels"):
        model.latent_fields(
            {"sp": {"alpha_foraging": 0.2, "alpha_moving": -0.1}},
            {grid.keys[0]: {}},
        )


def test_model_rejects_duplicate_parameter_names_across_processes():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    with pytest.raises(ValueError, match="duplicate parameter"):
        Model(
            grid,
            {
                "sp": (
                    LinearSuitability((), "shared", {}),
                    LinearActivity((), "shared", {}),
                )
            },
            (_presence_stream(grid),),
        )
