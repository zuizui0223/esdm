import importlib.util

import pytest


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def _fixture(n_space: int):
    from esdm.domain import Grid, StateSpace
    from esdm.model import Model
    from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
    from esdm.process import LinearActivity, LinearState, LinearSuitability

    grid = Grid(
        space=tuple(f"s{i}" for i in range(n_space)),
        doy=(15, 75, 135, 195, 255, 315),
        hour=(0, 6, 12, 18),
    )
    states = StateSpace(("resting", "foraging"))
    processes = (
        LinearSuitability(
            ("x", "z"),
            "intercept",
            {"x": "beta_x", "z": "beta_z"},
        ),
        LinearActivity(
            ("x",),
            "activity_intercept",
            {"x": "activity_beta_x"},
        ),
        LinearState(
            states,
            "resting",
            ("z",),
            {"foraging": "alpha_foraging"},
            {"foraging": {"z": "beta_foraging_z"}},
        ),
    )
    stream = StateAnnotatedCount(
        "annotated",
        state_space=states,
        effort=EffortField({key: 2.0 for key in grid.keys}),
        detection=KnownDetection(0.8),
        informs=frozenset({"suitability", "activity", "state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": processes}, (stream,))
    covariates = {
        key: {
            "x": (i % 31 - 15) / 10.0,
            "z": (i % 17 - 8) / 7.0,
        }
        for i, key in enumerate(grid.keys)
    }
    theta = {
        "sp": {
            "intercept": 0.2,
            "beta_x": 0.55,
            "beta_z": -0.25,
            "activity_intercept": -0.3,
            "activity_beta_x": 0.4,
            "alpha_foraging": 0.1,
            "beta_foraging_z": -0.35,
        }
    }
    theta_obs = {"annotated": {}}
    return model, covariates, theta, theta_obs


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_state_activity_array_trace_does_not_scale_with_2880_contexts():
    from esdm.benchmarks import array_trace_equation_count

    small = _fixture(2)    # 48 contexts
    large = _fixture(120)  # 2,880 contexts

    small_count = array_trace_equation_count(*small)
    large_count = array_trace_equation_count(*large)

    assert small_count > 0
    assert large_count <= small_count + 10
    assert large_count < 100
