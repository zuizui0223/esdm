import importlib.util

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_sbc_runner_uses_prior_simulate_fit_rank_cycle():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import run_numpyro_sbc
    from esdm.observe import EffortField, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))
    keys = grid.keys
    model = Model(
        domain=grid,
        species={
            "taxon": (
                LinearSuitability(
                    covariates=("env",),
                    intercept_parameter="intercept",
                    coefficient_parameters={"env": "beta_env"},
                ),
            )
        },
        streams=(
            PresenceOnly(
                name="records",
                effort=EffortField({key: 2.0 for key in keys}),
                informs=frozenset({"suitability"}),
            ),
        ),
    )
    covariates = {
        key: {"env": value}
        for key, value in zip(keys, (-1.0, -0.33, 0.33, 1.0), strict=True)
    }

    result = run_numpyro_sbc(
        model,
        covariates,
        replicates=2,
        rng_seed=19,
        num_warmup=30,
        num_samples=40,
        progress_bar=False,
    )

    assert set(result.ranks) == {
        "taxon.suitability.intercept",
        "taxon.suitability.beta_env",
    }
    for ranks in result.ranks.values():
        assert len(ranks) == 2
        assert all(0 <= rank <= 40 for rank in ranks)
    assert result.posterior_draw_count == 40
