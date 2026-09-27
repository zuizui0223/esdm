import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate import simulate_presence_only


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def _model():
    grid = Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
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
    model = Model(grid, {"sp": (process,)}, (opportunistic, calibrated))
    xs = (-1.5, -0.5, 0.5, 1.5)
    covariates = {key: {"x": xs[i]} for i, key in enumerate(grid.keys)}
    return model, covariates


def test_simulation_uses_declared_observation_effort_parameters():
    model, covariates = _model()
    generated = simulate_presence_only(
        model,
        {"sp": {"intercept": 1.0, "beta_x": 0.6}},
        covariates,
        theta_obs={"opportunistic": {"gamma_x": 0.7}},
        seed=10,
    )
    rates = generated.expected_rates["opportunistic"]["sp"]
    keys = model.domain.keys
    assert rates[keys[-1]] / rates[keys[0]] == pytest.approx(
        math.exp((0.6 + 0.7) * 3.0)
    )
    calibrated = generated.expected_rates["calibrated"]["sp"]
    assert calibrated[keys[-1]] / calibrated[keys[0]] == pytest.approx(
        math.exp(0.6 * 3.0)
    )


def test_simulation_rejects_missing_unknown_effort_parameter():
    model, covariates = _model()
    with pytest.raises(KeyError):
        simulate_presence_only(
            model,
            {"sp": {"intercept": 1.0, "beta_x": 0.6}},
            covariates,
            seed=10,
        )


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_numpyro_joint_fit_samples_ecological_and_observation_parameters():
    from esdm.model.backend_numpyro import fit_numpyro

    model, covariates = _model()
    generated = simulate_presence_only(
        model,
        {"sp": {"intercept": 1.5, "beta_x": 0.6}},
        covariates,
        theta_obs={"opportunistic": {"gamma_x": 0.7}},
        seed=22,
    )
    fit = fit_numpyro(
        model,
        generated.counts,
        covariates,
        rng_seed=23,
        num_warmup=80,
        num_samples=100,
        progress_bar=False,
    )
    assert "sp.suitability.intercept" in fit.samples
    assert "sp.suitability.beta_x" in fit.samples
    assert "stream.opportunistic.gamma_x" in fit.samples
    assert "stream.calibrated.gamma_x" not in fit.samples
