import importlib.util
import sys

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def _simple_model():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("s0", "s1", "s2", "s3"), doy=(1,), hour=(0,))
    keys = grid.keys
    process = LinearSuitability(
        covariates=("temp",),
        intercept_parameter="intercept",
        coefficient_parameters={"temp": "beta_temp"},
    )
    stream = PresenceOnly(
        name="records",
        effort=EffortField({key: 1.0 for key in keys}),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(domain=grid, species={"sp": (process,)}, streams=(stream,))
    covariates = {
        key: {"temp": value}
        for key, value in zip(keys, (-1.5, -0.5, 0.5, 1.5), strict=True)
    }
    data = {
        "records": {
            "sp": {
                key: count
                for key, count in zip(keys, (0, 1, 3, 8), strict=True)
            }
        }
    }
    return model, covariates, data


def test_numpyro_backend_module_is_optional_and_importable():
    from esdm.model.backend_numpyro import numpyro_available

    assert numpyro_available() is NUMPYRO_AVAILABLE
    if sys.version_info < (3, 11):
        assert numpyro_available() is False


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_numpyro_backend_recovers_simple_suitability_signal():
    from esdm.model.backend_numpyro import fit_numpyro

    model, covariates, data = _simple_model()
    fit = fit_numpyro(
        model,
        data,
        covariates,
        rng_seed=7,
        num_warmup=150,
        num_samples=200,
        num_chains=1,
        progress_bar=False,
    )

    slope_draws = fit.samples["sp.suitability.beta_temp"]
    assert len(slope_draws) == 200
    assert sum(float(x) for x in slope_draws) / len(slope_draws) > 0.25
    assert fit.num_divergences >= 0


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_posterior_predictive_rates_use_existing_stream_semantics():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import posterior_record_rates
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("a", "b"), doy=(1,), hour=(0,))
    keys = grid.keys
    model = Model(
        domain=grid,
        species={
            "sp": (
                LinearSuitability(
                    covariates=("x",),
                    intercept_parameter="intercept",
                    coefficient_parameters={"x": "beta_x"},
                ),
            )
        },
        streams=(
            PresenceOnly(
                name="records",
                effort=EffortField({keys[0]: 2.0, keys[1]: 4.0}),
                detection_probability=0.5,
                informs=frozenset({"suitability"}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    covariates = {keys[0]: {"x": 0.0}, keys[1]: {"x": 1.0}}

    rates = posterior_record_rates(
        model,
        {
            "sp.suitability.intercept": [0.0],
            "sp.suitability.beta_x": [0.0],
        },
        covariates,
    )
    assert rates[("records", "sp")] == ((1.0, 2.0),)
