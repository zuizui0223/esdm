import importlib.util

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_sbc_runner_records_ess_thinned_rank_support_for_all_free_parameters():
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import run_numpyro_sbc
    from esdm.observe import LogLinearEffort, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))
    keys = grid.keys
    model = Model(
        domain=grid,
        species={
            "taxon": (
                LinearSuitability(
                    covariates=("x",),
                    intercept_parameter="intercept",
                    coefficient_parameters={"x": "beta_x"},
                ),
            )
        },
        streams=(
            PresenceOnly(
                name="opportunistic",
                effort=LogLinearEffort(4.0, "x", "gamma_x"),
                informs=frozenset({"suitability"}),
                targets=frozenset({"taxon"}),
            ),
        ),
    )
    covariates = {
        key: {"x": value}
        for key, value in zip(keys, (-1.5, -0.5, 0.5, 1.5), strict=True)
    }

    result = run_numpyro_sbc(
        model,
        covariates,
        replicates=2,
        rng_seed=31,
        num_warmup=40,
        num_samples=60,
        num_chains=1,
        ess_thinning=True,
        progress_bar=False,
    )

    expected = {
        "taxon.suitability.intercept",
        "taxon.suitability.beta_x",
        "stream.opportunistic.gamma_x",
    }
    assert set(result.ranks) == expected
    assert set(result.draw_counts_by_site) == expected
    assert set(result.effective_sample_sizes_by_site) == expected
    for site in expected:
        assert len(result.ranks[site]) == 2
        assert len(result.draw_counts_by_site[site]) == 2
        assert len(result.effective_sample_sizes_by_site[site]) == 2
        for rank, draw_count, ess in zip(
            result.ranks[site],
            result.draw_counts_by_site[site],
            result.effective_sample_sizes_by_site[site],
        ):
            assert draw_count >= 1
            assert 0 <= rank <= draw_count
            assert ess > 0.0
