import importlib.util

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_numpyro_handles_partial_known_effort_stream_without_invalid_initialization():
    """Zero-exposure calibrated cells are absent observations, not Poisson(0) constraints."""

    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.model.backend_numpyro import fit_numpyro
    from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
    from esdm.process import LinearSuitability
    from esdm.simulate import simulate_presence_only

    grid = Grid(space=("a", "b", "c", "d"), doy=(1,), hour=(0,))
    keys = grid.keys
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    opportunistic = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(2.0, "x", "gamma_x"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    calibrated = PresenceOnly(
        name="calibrated",
        effort=EffortField({keys[0]: 3.0, keys[-1]: 3.0}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (process,)},
        streams=(opportunistic, calibrated),
    )
    covariates = {
        key: {"x": x}
        for key, x in zip(keys, (-1.5, -0.5, 0.5, 1.5), strict=True)
    }
    theta = {"sp": {"intercept": 0.2, "beta_x": 0.4}}
    theta_obs = {
        "opportunistic": {"gamma_x": 0.3},
        "calibrated": {},
    }
    generated = simulate_presence_only(
        model,
        theta,
        covariates,
        theta_obs=theta_obs,
        seed=17,
    )

    assert generated.expected_rates["calibrated"]["sp"][keys[1]] == 0.0
    assert generated.expected_rates["calibrated"]["sp"][keys[2]] == 0.0
    assert generated.counts["calibrated"]["sp"][keys[1]] == 0
    assert generated.counts["calibrated"]["sp"][keys[2]] == 0

    fit = fit_numpyro(
        model,
        generated.counts,
        covariates,
        rng_seed=18,
        num_warmup=20,
        num_samples=20,
        num_chains=1,
        progress_bar=False,
        target_accept_prob=0.9,
    )
    assert len(fit.samples["sp.suitability.beta_x"]) == 20
    assert len(fit.samples["stream.opportunistic.gamma_x"]) == 20
