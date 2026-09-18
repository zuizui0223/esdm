import importlib.util
import math
from dataclasses import dataclass

import pytest

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability, PriorSpec


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_practical_identification_api_is_public():
    from esdm.identify import PracticalIdentificationDiagnostic, diagnose_practical_identification

    assert PracticalIdentificationDiagnostic is not None
    assert callable(diagnose_practical_identification)


def _design(*, perturbation: float, calibrated: bool):
    xs = (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)
    pattern = (1.0, -1.0, 0.5, -0.5, 0.25, -0.25, 0.75)
    grid = Grid(space=tuple(f"s{i}" for i in range(len(xs))), doy=(1,), hour=(0,))
    covariates = {
        key: {"x": x, "h": x + perturbation * pattern[i]}
        for i, (key, x) in enumerate(zip(grid.keys, xs, strict=True))
    }
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    opportunistic = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(5.0, "h", "gamma_h"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    streams = [opportunistic]
    if calibrated:
        streams.append(
            PresenceOnly(
                name="calibrated",
                effort=EffortField({key: 3.0 for key in grid.keys}),
                informs=frozenset({"suitability"}),
                targets=frozenset({"sp"}),
            )
        )
    model = Model(grid, {"sp": (process,)}, tuple(streams))
    theta = {"sp": {"intercept": 0.3, "beta_x": 0.6}}
    theta_obs = {"opportunistic": {"gamma_h": 0.7}}
    return model, covariates, theta, theta_obs


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_exact_confounding_is_structurally_not_identified():
    from esdm.identify import identify_parameter_from_design

    model, covariates, theta, theta_obs = _design(perturbation=0.0, calibrated=False)
    result = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.suitability.beta_x",
        method="jax",
    )
    assert result.status is IdentificationStatus.NOT_IDENTIFIED
    assert any("jacobian_backend=jax.jacfwd" in value for value in result.evidence)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_near_confounding_is_structural_but_practically_weak():
    from esdm.identify import diagnose_practical_identification, identify_parameter_from_design

    model, covariates, theta, theta_obs = _design(perturbation=1e-6, calibrated=False)
    structural = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.suitability.beta_x",
        method="jax",
        rtol=1e-10,
    )
    practical = diagnose_practical_identification(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.suitability.beta_x",
        relative_singular_value_threshold=1e-4,
        condition_number_threshold=1e6,
    )
    assert structural.status is IdentificationStatus.IDENTIFIED
    assert practical.weak is True
    assert practical.relative_min_singular_value < 1e-4


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_calibrated_second_stream_restores_practical_identification():
    from esdm.identify import diagnose_practical_identification, identify_parameter_from_design

    model, covariates, theta, theta_obs = _design(perturbation=0.0, calibrated=True)
    structural = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.suitability.beta_x",
        method="jax",
    )
    practical = diagnose_practical_identification(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target="sp.suitability.beta_x",
        relative_singular_value_threshold=1e-4,
        condition_number_threshold=1e6,
    )
    assert structural.status is IdentificationStatus.IDENTIFIED
    assert practical.weak is False


@dataclass(frozen=True, slots=True)
class QuadraticEffort:
    covariate: str = "x"
    coefficient_parameter: str = "gamma"

    @property
    def requires(self):
        return frozenset({self.covariate})

    def priors(self):
        return {self.coefficient_parameter: PriorSpec("Normal", {"loc": 0.0, "scale": 1.0})}

    def at(self, key, *, theta, covariates, exp_fn=math.exp):
        return exp_fn(theta[self.coefficient_parameter] ** 2 * covariates[key][self.covariate])

    def array(self, keys, *, theta, covariates, array_module):
        x = array_module.asarray([covariates[key][self.covariate] for key in keys])
        return array_module.exp(theta[self.coefficient_parameter] ** 2 * x)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_exact_autodiff_does_not_invent_quadratic_sensitivity_at_zero():
    from esdm.identify import identify_parameter_from_design

    grid = Grid(space=("a", "b", "c"), doy=(1,), hour=(0,))
    process = LinearSuitability((), "intercept", {})
    stream = PresenceOnly(
        name="records",
        effort=QuadraticEffort(),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": (process,)}, (stream,))
    covariates = {
        grid.keys[0]: {"x": -1.0},
        grid.keys[1]: {"x": 0.5},
        grid.keys[2]: {"x": 2.0},
    }
    result = identify_parameter_from_design(
        model,
        covariates,
        theta={"sp": {"intercept": 0.2}},
        theta_obs={"records": {"gamma": 0.0}},
        target="stream.records.gamma",
        method="jax",
    )
    assert result.status is IdentificationStatus.DESIGN_UNINFORMED
