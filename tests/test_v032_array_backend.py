import importlib.util

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _fixture():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.observe import LogLinearEffort, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("a", "b", "c"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariates=("x", "z"),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x", "z": "beta_z"},
    )
    stream = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(2.5, "x", "gamma_x"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": (process,)}, (stream,))
    covariates = {
        grid.keys[0]: {"x": -1.0, "z": 0.5},
        grid.keys[1]: {"x": 0.0, "z": -0.25},
        grid.keys[2]: {"x": 1.5, "z": 1.0},
    }
    theta = {"sp": {"intercept": 0.4, "beta_x": 0.7, "beta_z": -0.2}}
    theta_obs = {"opportunistic": {"gamma_x": -0.35}}
    return model, covariates, theta, theta_obs


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_array_latent_fields_and_rates_match_mapping_path():
    import jax.numpy as jnp

    model, covariates, theta, theta_obs = _fixture()
    scalar_fields = model.latent_fields(theta, covariates)
    scalar_rates = model.streams[0].expected_rates(
        "sp",
        scalar_fields,
        theta_obs=theta_obs["opportunistic"],
        covariates=covariates,
    )

    array_fields = model.latent_field_arrays(
        theta,
        covariates,
        array_module=jnp,
    )
    assert array_fields.log_intensity["sp"].keys == model.domain.keys
    assert list(map(float, array_fields.log_intensity["sp"].values)) == pytest.approx(
        [scalar_fields.log_intensity["sp"][key] for key in model.domain.keys]
    )

    array_rates = model.streams[0].expected_rate_array(
        "sp",
        array_fields,
        theta_obs=theta_obs["opportunistic"],
        covariates=covariates,
        array_module=jnp,
    )
    assert array_rates.keys == model.domain.keys
    assert list(map(float, array_rates.values)) == pytest.approx(
        [scalar_rates[key] for key in model.domain.keys]
    )


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_array_knockout_preserves_baseline_and_neutralizes_slopes():
    import jax.numpy as jnp

    model, covariates, _theta, _theta_obs = _fixture()
    knocked = model.knockout("sp", "suitability")
    fields = knocked.latent_field_arrays(
        {"sp": {"intercept": 0.4}},
        covariates,
        array_module=jnp,
    )
    assert fields.log_intensity["sp"].keys == model.domain.keys
    assert list(map(float, fields.log_intensity["sp"].values)) == pytest.approx(
        [0.4, 0.4, 0.4]
    )
