import importlib.util
import sys

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def test_numpyro_backend_import_is_optional_on_python310():
    if sys.version_info < (3, 11):
        from esdm.model.backend_numpyro import numpyro_available

        assert numpyro_available() is False


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_numpyro_backend_recovers_simple_suitability_signal():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import fit_numpyro
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("s0", "s1", "s2", "s3"), doy=(1,), hour=(0,))
    process = LinearSuitability(
        covariate="temp",
        intercept_prior=(0.0, 1.0),
        slope_prior=(0.0, 1.0),
    )
    stream = PresenceOnly(
        name="records",
        species="sp",
        effort=EffortField((1.0, 1.0, 1.0, 1.0)),
        detection=1.0,
        informs=frozenset({"suitability"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (process,)},
        streams=(stream,),
        covariates={"temp": (-1.5, -0.5, 0.5, 1.5)},
    )

    data = {"records": (0, 1, 3, 8)}
    fit = fit_numpyro(
        model,
        data,
        rng_seed=7,
        num_warmup=150,
        num_samples=200,
        num_chains=1,
        progress_bar=False,
    )

    slope_draws = fit.samples["sp.suitability.slope"]
    assert len(slope_draws) == 200
    assert sum(float(x) for x in slope_draws) / len(slope_draws) > 0.25


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_posterior_predictive_rates_use_existing_stream_semantics():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import posterior_record_rates
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    model = Model(
        domain=Grid(space=("a", "b"), doy=(1,), hour=(0,)),
        species={
            "sp": (
                LinearSuitability(
                    covariate="x",
                    intercept_prior=(0.0, 1.0),
                    slope_prior=(0.0, 1.0),
                ),
            )
        },
        streams=(
            PresenceOnly(
                name="records",
                species="sp",
                effort=EffortField((2.0, 4.0)),
                detection=0.5,
                informs=frozenset({"suitability"}),
            ),
        ),
        covariates={"x": (0.0, 1.0)},
    )

    rates = posterior_record_rates(
        model,
        {"sp.suitability.intercept": [0.0], "sp.suitability.slope": [0.0]},
    )
    assert rates["records"] == ((1.0, 2.0),)
