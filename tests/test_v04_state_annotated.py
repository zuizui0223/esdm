import math

import pytest

from esdm.domain import Grid, StateSpace
from esdm.model import DesignUninformedError, Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability


def _annotated_fixture(*, effort_value=4.0, detection=None):
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    if detection is None:
        detection = KnownDetection(0.5)
    stream = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({grid.keys[0]: effort_value}),
        detection=detection,
        informs=frozenset({"suitability", "activity", "state"}),
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
    theta = {
        "sp": {
            "intercept": math.log(3.0),
            "activity_intercept": 0.0,
            "alpha_foraging": math.log(3.0),
        }
    }
    covariates = {grid.keys[0]: {}}
    return grid, states, stream, model, theta, covariates


def test_annotated_rates_factor_intensity_activity_state_effort_detection():
    grid, _states, stream, model, theta, covariates = _annotated_fixture()
    model.check_design()
    fields = model.latent_fields(theta, covariates)

    blocks = stream.observation_blocks(
        "sp",
        fields,
        covariates=covariates,
    )

    assert tuple(block.name for block in blocks) == (
        "annotated.sp.resting",
        "annotated.sp.foraging",
    )
    assert tuple(float(block.rates[0]) for block in blocks) == pytest.approx(
        (0.75, 2.25)
    )
    assert sum(float(block.rates[0]) for block in blocks) == pytest.approx(3.0)




def test_known_detection_accepts_probability_keyword():
    detection = KnownDetection(probability=0.5)

    assert detection.probability({}) == pytest.approx(0.5)

def test_logit_detection_is_an_observation_parameter():
    detection = LogitDetection("detection_intercept")

    assert set(detection.priors()) == {"detection_intercept"}
    assert detection.probability({"detection_intercept": 0.0}) == pytest.approx(0.5)


def test_annotated_data_requires_exact_states_and_nonnegative_counts():
    grid, _states, stream, model, theta, covariates = _annotated_fixture()
    fields = model.latent_fields(theta, covariates)
    key = grid.keys[0]

    with pytest.raises(ValueError, match="state labels"):
        stream.observation_blocks(
            "sp",
            fields,
            data={"resting": {key: 1}},
            covariates=covariates,
        )

    with pytest.raises(ValueError, match="non-negative"):
        stream.observation_blocks(
            "sp",
            fields,
            data={"resting": {key: -1}, "foraging": {key: 0}},
            covariates=covariates,
        )


def test_positive_annotated_count_at_zero_exposure_fails_closed():
    grid, _states, stream, model, theta, covariates = _annotated_fixture(
        effort_value=0.0
    )
    fields = model.latent_fields(theta, covariates)
    key = grid.keys[0]

    with pytest.raises(ValueError, match="zero-exposure"):
        stream.observation_blocks(
            "sp",
            fields,
            data={"resting": {key: 1}, "foraging": {key: 0}},
            covariates=covariates,
        )


@pytest.mark.parametrize("include_activity,include_state", [(False, False), (True, False)])
def test_annotated_stream_requires_activity_and_state_processes(
    include_activity,
    include_state,
):
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    processes = [LinearSuitability((), "intercept", {})]
    if include_activity:
        processes.append(LinearActivity((), "activity_intercept", {}))
    if include_state:
        processes.append(
            LinearState(
                states,
                "resting",
                (),
                {"foraging": "alpha_foraging"},
                {"foraging": {}},
            )
        )
    stream = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({grid.keys[0]: 1.0}),
        detection=KnownDetection(1.0),
        informs=frozenset({"suitability", "activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": tuple(processes)}, (stream,))

    with pytest.raises(DesignUninformedError, match="latent channel"):
        model.check_design()


def test_presence_only_rate_ignores_declared_activity_and_state_channels():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 2.0}),
        detection_probability=0.5,
        informs=frozenset({"suitability"}),
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
    fields = model.latent_fields(
        {
            "sp": {
                "intercept": math.log(5.0),
                "activity_intercept": -20.0,
                "alpha_foraging": 10.0,
            }
        },
        {grid.keys[0]: {}},
    )

    rates = stream.expected_rates(
        "sp",
        fields,
        covariates={grid.keys[0]: {}},
    )

    assert rates[grid.keys[0]] == pytest.approx(5.0)
