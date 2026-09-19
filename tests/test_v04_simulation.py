import math

from esdm.domain import Grid, StateSpace
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability
from esdm.simulate import simulate_observations, simulate_presence_only


def _presence_fixture():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 1.0, grid.keys[1]: 2.0}),
        detection_probability=0.5,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (stream,),
    )
    theta = {"sp": {"intercept": math.log(2.0)}}
    covariates = {key: {} for key in grid.keys}
    return model, theta, covariates


def _annotated_fixture():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    states = StateSpace(("resting", "foraging"))
    stream = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({key: 2.0 for key in grid.keys}),
        detection=KnownDetection(1.0),
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
    covariates = {key: {} for key in grid.keys}
    return model, theta, covariates


def test_generic_simulator_matches_presence_only_compatibility_wrapper():
    model, theta, covariates = _presence_fixture()

    generic = simulate_observations(
        model,
        theta,
        covariates,
        seed=17,
    )
    legacy = simulate_presence_only(
        model,
        theta,
        covariates,
        seed=17,
    )

    assert generic.counts == legacy.counts
    assert generic.expected_rates == legacy.expected_rates


def test_generic_simulator_generates_state_annotated_blocks():
    model, theta, covariates = _annotated_fixture()

    generated = simulate_observations(
        model,
        theta,
        covariates,
        seed=23,
    )

    assert set(generated.counts["annotated"]["sp"]) == {
        "resting",
        "foraging",
    }
    assert set(generated.expected_rates["annotated"]["sp"]) == {
        "resting",
        "foraging",
    }
    for state in ("resting", "foraging"):
        assert set(generated.counts["annotated"]["sp"][state]) == set(
            model.domain.keys
        )
        assert all(
            count >= 0
            for count in generated.counts["annotated"]["sp"][state].values()
        )

    first_key = model.domain.keys[0]
    assert generated.expected_rates["annotated"]["sp"]["resting"][
        first_key
    ] == 0.75
    assert generated.expected_rates["annotated"]["sp"]["foraging"][
        first_key
    ] == 2.25
