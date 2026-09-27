import importlib.util

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_array_trace_equation_count_is_public():
    from esdm.benchmarks import array_trace_equation_count

    assert callable(array_trace_equation_count)


def _fixture(n_space: int):
    from esdm.domain import Grid
    from esdm.model import Model
    from esdm.observe import LogLinearEffort, PresenceOnly
    from esdm.process import LinearSuitability

    grid = Grid(
        space=tuple(f"s{i}" for i in range(n_space)),
        doy=(15, 75, 135, 195, 255, 315),
        hour=(0, 6, 12, 18),
    )
    process = LinearSuitability(
        covariates=("x", "z"),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x", "z": "beta_z"},
    )
    stream = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(2.0, "x", "gamma_x"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": (process,)}, (stream,))
    covariates = {
        key: {
            "x": (i % 31 - 15) / 10.0,
            "z": (i % 17 - 8) / 7.0,
        }
        for i, key in enumerate(grid.keys)
    }
    theta = {"sp": {"intercept": 0.2, "beta_x": 0.55, "beta_z": -0.25}}
    theta_obs = {"opportunistic": {"gamma_x": 0.4}}
    return model, covariates, theta, theta_obs


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_array_trace_does_not_scale_with_2880_contexts():
    from esdm.benchmarks import array_trace_equation_count

    small = _fixture(2)  # 48 contexts
    large = _fixture(120)  # 2,880 contexts

    small_count = array_trace_equation_count(*small)
    large_count = array_trace_equation_count(*large)

    assert small_count > 0
    assert large_count <= small_count + 5
    assert large_count < 50
