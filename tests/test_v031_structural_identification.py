from esdm.domain import Grid
from esdm.identify import IdentificationStatus, identify_parameter_from_design
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability


def _grid():
    return Grid(space=("a", "b", "c", "d", "e"), doy=(1,), hour=(0,))


def _covariates(grid):
    xs = (-2.0, -1.0, 0.0, 1.0, 2.0)
    return {key: {"x": xs[i]} for i, key in enumerate(grid.keys)}


def _process():
    return LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )


def _opportunistic():
    return PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(5.0, "x", "gamma_x"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )


def _calibrated(grid):
    return PresenceOnly(
        name="calibrated",
        effort=EffortField({key: 3.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )


def _theta():
    return {"sp": {"intercept": 1.0, "beta_x": 0.6}}


def _theta_obs():
    return {"opportunistic": {"gamma_x": 0.7}}


def test_unknown_effort_gradient_makes_ecological_slope_structurally_not_identified():
    grid = _grid()
    model = Model(grid, {"sp": (_process(),)}, (_opportunistic(),))
    covariates = _covariates(grid)

    beta = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="sp.suitability.beta_x",
    )
    gamma = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="stream.opportunistic.gamma_x",
    )
    intercept = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="sp.suitability.intercept",
    )

    assert beta.status is IdentificationStatus.NOT_IDENTIFIED
    assert gamma.status is IdentificationStatus.NOT_IDENTIFIED
    assert intercept.status is IdentificationStatus.IDENTIFIED


def test_calibrated_second_stream_restores_structural_identification():
    grid = _grid()
    model = Model(
        grid,
        {"sp": (_process(),)},
        (_opportunistic(), _calibrated(grid)),
    )
    covariates = _covariates(grid)

    beta = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="sp.suitability.beta_x",
    )
    gamma = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="stream.opportunistic.gamma_x",
    )

    assert beta.status is IdentificationStatus.IDENTIFIED
    assert gamma.status is IdentificationStatus.IDENTIFIED


def test_design_uninformed_parameter_is_distinguished_from_confounded_parameter():
    grid = _grid()
    model = Model(grid, {"sp": (_process(),)}, (_opportunistic(),))
    covariates = _covariates(grid)
    result = identify_parameter_from_design(
        model,
        covariates,
        theta=_theta(),
        theta_obs=_theta_obs(),
        target="does.not.exist",
    )
    assert result.status is IdentificationStatus.DESIGN_UNINFORMED
