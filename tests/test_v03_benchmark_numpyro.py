import importlib.util

import pytest


NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


@pytest.mark.skipif(not NUMPYRO_AVAILABLE, reason="NumPyro optional backend not installed")
def test_fit_v03_world_returns_canonical_parameter_draws():
    from esdm.simulate.benchmark_v03 import make_correct_effort_world
    from esdm.validate.benchmark import fit_v03_world_numpyro

    result = fit_v03_world_numpyro(
        make_correct_effort_world(seed=17),
        rng_seed=17,
        num_warmup=40,
        num_samples=50,
        progress_bar=False,
    )

    assert result.world_name == "correct_effort"
    assert set(result.parameter_draws) == {"alpha", "beta"}
    assert len(result.parameter_draws["alpha"]) == 50
    assert len(result.parameter_draws["beta"]) == 50
    assert result.num_divergences >= 0
