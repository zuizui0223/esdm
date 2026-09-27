import math

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability


def _grid():
    return Grid(space=("a", "b", "c"), doy=(1,), hour=(0,))


def _covariates(grid):
    values = (-1.0, 0.0, 1.0)
    return {key: {"x": values[i]} for i, key in enumerate(grid.keys)}


def _process():
    return LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )


def test_fixed_effort_is_parameter_free_observation_model():
    grid = _grid()
    effort = EffortField({key: 5.0 for key in grid.keys})
    assert effort.priors() == {}
    assert effort.requires == frozenset()
    assert effort.at(grid.keys[0], theta={}, covariates=_covariates(grid)) == pytest.approx(5.0)


def test_loglinear_effort_is_observation_parameter_not_ecological_parameter():
    grid = _grid()
    effort = LogLinearEffort(
        baseline=5.0,
        covariate="x",
        coefficient_parameter="gamma_x",
    )
    assert set(effort.priors()) == {"gamma_x"}
    assert effort.requires == frozenset({"x"})
    covariates = _covariates(grid)
    low = effort.at(grid.keys[0], theta={"gamma_x": 0.7}, covariates=covariates)
    high = effort.at(grid.keys[-1], theta={"gamma_x": 0.7}, covariates=covariates)
    assert low == pytest.approx(5.0 * math.exp(-0.7))
    assert high == pytest.approx(5.0 * math.exp(0.7))


def test_presence_only_stream_exposes_effort_priors_and_uses_them_in_rates():
    grid = _grid()
    effort = LogLinearEffort(
        baseline=5.0,
        covariate="x",
        coefficient_parameter="gamma_x",
    )
    stream = PresenceOnly(
        name="opportunistic",
        effort=effort,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    assert set(stream.priors()) == {"gamma_x"}
    model = Model(grid, {"sp": (_process(),)}, (stream,))
    covariates = _covariates(grid)
    fields = model.latent_fields(
        {"sp": {"intercept": 0.0, "beta_x": 0.6}},
        covariates,
    )
    rates = stream.expected_rates(
        "sp",
        fields,
        theta_obs={"gamma_x": 0.7},
        covariates=covariates,
    )
    ratio = rates[grid.keys[-1]] / rates[grid.keys[0]]
    assert ratio == pytest.approx(math.exp(2.0 * (0.6 + 0.7)))


def test_two_stream_design_can_share_ecological_field_but_have_distinct_effort_models():
    grid = _grid()
    opportunistic = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(5.0, "x", "gamma_x"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    calibrated = PresenceOnly(
        name="calibrated",
        effort=EffortField({key: 3.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": (_process(),)}, (opportunistic, calibrated))
    assert model.check_design().informed_processes == (("sp", "suitability"),)
    assert set(opportunistic.priors()) == {"gamma_x"}
    assert calibrated.priors() == {}
