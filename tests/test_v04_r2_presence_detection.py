import math

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    MultiLogLinearEffort,
    PresenceOnly,
)
from esdm.process import LinearSuitability


def _fields():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    model = Model(
        grid,
        {"sp": (LinearSuitability((), "intercept", {}),)},
        (
            PresenceOnly(
                "legacy",
                effort=EffortField({grid.keys[0]: 2.0}),
                detection_probability=0.5,
                informs=frozenset({"suitability"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    fields = model.latent_fields(
        {"sp": {"intercept": math.log(3.0)}},
        {grid.keys[0]: {}},
    )
    return grid, fields


def test_presence_only_legacy_detection_probability_is_unchanged():
    grid, fields = _fields()
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 2.0}),
        detection_probability=0.5,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )

    rates = stream.expected_rates(
        "sp",
        fields,
        covariates={grid.keys[0]: {}},
    )

    assert rates[grid.keys[0]] == pytest.approx(3.0)
    assert stream.priors() == {}


def test_presence_only_can_use_unknown_detection_model():
    grid, fields = _fields()
    stream = PresenceOnly(
        "records",
        effort=EffortField({grid.keys[0]: 2.0}),
        detection=LogitDetection("detection_intercept"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )

    rates = stream.expected_rates(
        "sp",
        fields,
        theta_obs={"detection_intercept": 0.0},
        covariates={grid.keys[0]: {}},
    )

    assert rates[grid.keys[0]] == pytest.approx(3.0)
    assert set(stream.priors()) == {"detection_intercept"}


def test_presence_only_combines_unknown_effort_and_detection_priors():
    grid, fields = _fields()
    effort = MultiLogLinearEffort(
        baseline=4.0,
        covariates=("x",),
        coefficient_parameters={"x": "gamma_x"},
    )
    stream = PresenceOnly(
        "records",
        effort=effort,
        detection=LogitDetection("detection_intercept"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    key = grid.keys[0]
    theta_obs = {"gamma_x": 0.2, "detection_intercept": 0.0}
    covariates = {key: {"x": 1.0}}

    rates = stream.expected_rates(
        "sp",
        fields,
        theta_obs=theta_obs,
        covariates=covariates,
    )

    assert rates[key] == pytest.approx(
        3.0 * 4.0 * math.exp(0.2) * 0.5
    )
    assert set(stream.priors()) == {"gamma_x", "detection_intercept"}
    assert stream.requires == frozenset({"x"})


def test_presence_only_rejects_ambiguous_legacy_and_explicit_detection():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))

    with pytest.raises(ValueError, match="detection_probability"):
        PresenceOnly(
            "records",
            effort=EffortField({grid.keys[0]: 1.0}),
            detection_probability=0.7,
            detection=KnownDetection(probability=0.8),
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        )


def test_presence_only_rejects_effort_detection_parameter_collision():
    grid = Grid(space=("a",), doy=(1,), hour=(0,))
    effort = MultiLogLinearEffort(
        baseline=1.0,
        covariates=("x",),
        coefficient_parameters={"x": "shared"},
    )

    with pytest.raises(ValueError, match="overlap"):
        PresenceOnly(
            "records",
            effort=effort,
            detection=LogitDetection("shared"),
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        )


def test_presence_only_explicit_zero_detection_has_no_structural_exposure():
    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    stream = PresenceOnly(
        "records",
        effort=EffortField({key: 1.0 for key in grid.keys}),
        detection=KnownDetection(probability=0.0),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )

    assert stream.structural_exposure_mask(grid.keys) == (False, False)
