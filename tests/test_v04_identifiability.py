import importlib.util

import pytest

from esdm.domain import Grid, StateSpace
from esdm.identify import IdentificationStatus
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _fixture(*, unknown_detection: bool):
    grid = Grid(
        space=("s0", "s1", "s2", "s3", "s4"),
        doy=(1,),
        hour=(0,),
    )
    states = StateSpace(("resting", "foraging"))
    processes = (
        LinearSuitability(
            ("x",),
            "intercept",
            {"x": "beta_x"},
        ),
        LinearActivity(
            ("x",),
            "activity_intercept",
            {"x": "activity_beta_x"},
        ),
        LinearState(
            states,
            "resting",
            ("z",),
            {"foraging": "alpha_foraging"},
            {"foraging": {"z": "beta_foraging_z"}},
        ),
    )
    presence = PresenceOnly(
        "records",
        effort=EffortField({key: 5.0 for key in grid.keys}),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    detection = (
        LogitDetection("detection_intercept")
        if unknown_detection
        else KnownDetection(0.8)
    )
    annotated = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({key: 4.0 for key in grid.keys}),
        detection=detection,
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": processes},
        (presence, annotated),
    )
    xs = (-2.0, -1.0, 0.0, 1.0, 2.0)
    zs = (1.5, -1.0, 0.25, 1.0, -1.5)
    covariates = {
        key: {"x": x, "z": z}
        for key, x, z in zip(grid.keys, xs, zs, strict=True)
    }
    theta = {
        "sp": {
            "intercept": 0.2,
            "beta_x": 0.35,
            "activity_intercept": -0.3,
            "activity_beta_x": 0.55,
            "alpha_foraging": 0.1,
            "beta_foraging_z": -0.45,
        }
    }
    theta_obs = (
        {"annotated": {"detection_intercept": 0.25}}
        if unknown_detection
        else {}
    )
    return model, covariates, theta, theta_obs


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_known_detection_identifies_activity_and_state_slopes():
    from esdm.identify import identify_parameter_from_design

    model, covariates, theta, theta_obs = _fixture(unknown_detection=False)

    activity = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.activity.activity_beta_x",
        method="jax",
    )
    state = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.state.beta_foraging_z",
        method="jax",
    )

    assert activity.status is IdentificationStatus.IDENTIFIED
    assert state.status is IdentificationStatus.IDENTIFIED


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_unknown_detection_and_activity_intercept_are_structurally_not_identified():
    from esdm.identify import identify_parameter_from_design

    model, covariates, theta, theta_obs = _fixture(unknown_detection=True)

    activity = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.activity.activity_intercept",
        method="jax",
    )
    detection = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="stream.annotated.detection_intercept",
        method="jax",
    )

    assert activity.status is IdentificationStatus.NOT_IDENTIFIED
    assert detection.status is IdentificationStatus.NOT_IDENTIFIED
