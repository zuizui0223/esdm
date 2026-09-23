import math

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import DesignUninformedError, Model
from esdm.observe import EffortField, StateCompositionCount
from esdm.process import LinearActivity, LinearState, LinearSuitability


def _fixture(*, effort=4.0):
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    stream = StateCompositionCount(
        "state_calibration",
        state_space=states,
        effort=EffortField({grid.keys[0]: effort}),
        informs=frozenset({"state"}),
        targets=frozenset({"sp"}),
    )
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
        (stream,),
    )
    covariates = {grid.keys[0]: {}}
    return grid, stream, model, covariates


def test_state_composition_rates_sum_to_declared_label_effort():
    grid, stream, model, covariates = _fixture(effort=4.0)
    theta = {
        "sp": {
            "intercept": math.log(100.0),
            "activity_intercept": -8.0,
            "alpha_foraging": math.log(3.0),
        }
    }
    fields = model.latent_fields(theta, covariates)

    blocks = stream.observation_blocks("sp", fields, covariates=covariates)

    assert tuple(block.name for block in blocks) == (
        "state_calibration.sp.resting",
        "state_calibration.sp.foraging",
    )
    assert tuple(float(block.rates[0]) for block in blocks) == pytest.approx(
        (1.0, 3.0)
    )
    assert sum(float(block.rates[0]) for block in blocks) == pytest.approx(4.0)


def test_state_composition_is_independent_of_intensity_and_activity():
    _grid, stream, model, covariates = _fixture(effort=2.0)
    theta_a = {
        "sp": {
            "intercept": -20.0,
            "activity_intercept": -20.0,
            "alpha_foraging": 0.4,
        }
    }
    theta_b = {
        "sp": {
            "intercept": 20.0,
            "activity_intercept": 20.0,
            "alpha_foraging": 0.4,
        }
    }

    rates = []
    for theta in (theta_a, theta_b):
        fields = model.latent_fields(theta, covariates)
        blocks = stream.observation_blocks("sp", fields, covariates=covariates)
        rates.append(tuple(float(block.rates[0]) for block in blocks))

    assert rates[0] == pytest.approx(rates[1])


def test_state_composition_positive_count_at_zero_exposure_fails_closed():
    grid, stream, model, covariates = _fixture(effort=0.0)
    fields = model.latent_fields(
        {
            "sp": {
                "intercept": 0.0,
                "activity_intercept": 0.0,
                "alpha_foraging": 0.0,
            }
        },
        covariates,
    )
    key = grid.keys[0]

    with pytest.raises(ValueError, match="zero-exposure"):
        stream.observation_blocks(
            "sp",
            fields,
            data={"resting": {key: 1}, "foraging": {key: 0}},
            covariates=covariates,
        )


def test_state_composition_requires_state_channel_but_not_activity_channel():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    stream = StateCompositionCount(
        "state_calibration",
        state_space=states,
        effort=EffortField({grid.keys[0]: 1.0}),
        informs=frozenset({"state"}),
        targets=frozenset({"sp"}),
    )

    state_only = Model(
        grid,
        {
            "sp": (
                LinearState(
                    states,
                    "resting",
                    (),
                    {"foraging": "alpha_foraging"},
                    {"foraging": {}},
                ),
            )
        },
        (stream,),
    )
    state_only.check_design()

    missing_state = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (stream,),
    )
    with pytest.raises(DesignUninformedError, match="latent channel"):
        missing_state.check_design()


def test_state_composition_validates_exact_state_labels():
    grid, stream, model, covariates = _fixture()
    fields = model.latent_fields(
        {
            "sp": {
                "intercept": 0.0,
                "activity_intercept": 0.0,
                "alpha_foraging": 0.0,
            }
        },
        covariates,
    )

    with pytest.raises(ValueError, match="state labels"):
        stream.observation_blocks(
            "sp",
            fields,
            data={"resting": {grid.keys[0]: 1}},
            covariates=covariates,
        )
