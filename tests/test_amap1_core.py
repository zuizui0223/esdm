import importlib.util
import math

import pytest

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import (
    AdaptiveCoherenceMapField,
    ExchangeableMapField,
    FixedCoherenceMapField,
    LinearSuitability,
)
from esdm.validate.map1_known_truth import make_map1_fixture


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None
NUMPYRO_AVAILABLE = importlib.util.find_spec("numpyro") is not None


def _theta(process, *, sigma=1.0, coherence=None, active=None):
    theta = {process.sigma_parameter: float(sigma)}
    if isinstance(process, AdaptiveCoherenceMapField):
        theta[process.coherence_parameter] = float(coherence)
    dimension = process.graph.node_count - 1
    for index in range(dimension):
        theta[process.innovation_parameter(index)] = (
            1.0 if active == index else 0.0
        )
    return theta


def _node_covariance(process, *, coherence=None):
    dimension = process.graph.node_count - 1
    columns = []
    for active in range(dimension):
        columns.append(
            process.node_field(
                _theta(
                    process,
                    sigma=1.0,
                    coherence=coherence,
                    active=active,
                )
            )
        )
    n = process.graph.node_count
    return tuple(
        tuple(
            math.fsum(
                columns[column][i] * columns[column][j]
                for column in range(dimension)
            )
            for j in range(n)
        )
        for i in range(n)
    )


def _trace(matrix):
    return math.fsum(matrix[i][i] for i in range(len(matrix)))


def test_amap1_prior_surface_is_bounded_and_interpretation_neutral():
    fixture = make_map1_fixture()
    process = AdaptiveCoherenceMapField(fixture.graph)
    priors = process.priors()

    assert priors[process.sigma_parameter].distribution == "HalfNormal"
    assert priors[process.coherence_parameter].distribution == "Beta"
    assert priors[process.coherence_parameter].parameters == {
        "alpha": 1.0,
        "beta": 1.0,
    }
    assert (
        sum(name.startswith(process.innovation_prefix) for name in priors)
        == fixture.graph.node_count - 1
    )


def test_amap1_covariance_endpoints_match_map1_controls():
    fixture = make_map1_fixture()
    adaptive = AdaptiveCoherenceMapField(fixture.graph)
    exchangeable = ExchangeableMapField(fixture.graph)
    coherent = FixedCoherenceMapField(
        fixture.graph,
        fixed_rho=adaptive.fixed_rho,
        alpha=adaptive.alpha,
    )

    cov_zero = _node_covariance(adaptive, coherence=0.0)
    cov_one = _node_covariance(adaptive, coherence=1.0)
    cov_exchangeable = _node_covariance(exchangeable)
    cov_coherent = _node_covariance(coherent)

    for i in range(fixture.graph.node_count):
        for j in range(fixture.graph.node_count):
            assert cov_zero[i][j] == pytest.approx(
                cov_exchangeable[i][j],
                rel=1e-9,
                abs=1e-9,
            )
            assert cov_one[i][j] == pytest.approx(
                cov_coherent[i][j],
                rel=1e-9,
                abs=1e-9,
            )


def test_amap1_coherence_changes_structure_not_total_prior_energy():
    fixture = make_map1_fixture()
    adaptive = AdaptiveCoherenceMapField(fixture.graph)
    expected = fixture.graph.node_count - 1

    for coherence in (0.0, 0.2, 0.5, 0.8, 1.0):
        covariance = _node_covariance(
            adaptive,
            coherence=coherence,
        )
        assert _trace(covariance) == pytest.approx(
            expected,
            rel=1e-9,
            abs=1e-9,
        )


def test_amap1_field_is_exact_zero_sum():
    fixture = make_map1_fixture()
    process = AdaptiveCoherenceMapField(fixture.graph)
    theta = {
        process.sigma_parameter: 0.7,
        process.coherence_parameter: 0.4,
    }
    for index in range(fixture.graph.node_count - 1):
        theta[process.innovation_parameter(index)] = math.sin(index + 0.4)

    values = process.node_field(theta)
    assert math.fsum(values) == pytest.approx(0.0, abs=1e-10)


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_amap1_field_is_differentiable_in_sigma_and_coherence():
    import jax
    import jax.numpy as jnp

    fixture = make_map1_fixture()
    process = AdaptiveCoherenceMapField(fixture.graph)
    innovations = {
        process.innovation_parameter(index): math.cos(index + 0.1)
        for index in range(fixture.graph.node_count - 1)
    }

    def objective(values):
        theta = {
            process.sigma_parameter: values[0],
            process.coherence_parameter: values[1],
            **innovations,
        }
        field = process.node_field_array(theta, array_module=jnp)
        return jnp.sum(field * field)

    gradient = jax.grad(objective)(jnp.asarray([0.6, 0.4]))
    assert tuple(gradient.shape) == (2,)
    assert bool(jnp.all(jnp.isfinite(gradient)))
    assert abs(float(gradient[0])) > 1e-8
    assert abs(float(gradient[1])) > 1e-8


@pytest.mark.skipif(
    not NUMPYRO_AVAILABLE,
    reason="NumPyro optional backend not installed",
)
def test_amap1_uses_existing_numpyro_graph_with_beta_coherence_prior():
    import jax.random as random
    import numpyro.handlers as handlers

    from esdm.model.backend_numpyro import make_numpyro_model
    from esdm.simulate import simulate_presence_only

    fixture = make_map1_fixture()
    spaces = fixture.grid.space[:5]
    grid = Grid(space=spaces, doy=(60,), hour=(12,))
    process = AdaptiveCoherenceMapField(fixture.graph)
    model = Model(
        grid,
        {
            "sp": (
                LinearSuitability(
                    covariates=("mean_env",),
                    intercept_parameter="intercept",
                    coefficient_parameters={"mean_env": "beta_mean_env"},
                ),
                process,
            )
        },
        (
            PresenceOnly(
                "records",
                effort=EffortField({key: 3.0 for key in grid.keys}),
                detection_probability=1.0,
                informs=frozenset({"suitability", process.name}),
                targets=frozenset({"sp"}),
            ),
        ),
    )
    covariates = {
        key: {"mean_env": fixture.covariates[key]["mean_env"]}
        for key in grid.keys
    }
    theta = {
        "sp": {
            "intercept": 0.2,
            "beta_mean_env": 0.3,
            process.sigma_parameter: 0.5,
            process.coherence_parameter: 0.35,
        }
    }
    for index in range(fixture.graph.node_count - 1):
        theta["sp"][process.innovation_parameter(index)] = (
            0.25 * math.sin(index + 0.2)
        )

    generated = simulate_presence_only(
        model,
        theta,
        covariates,
        seed=123,
    )
    program = make_numpyro_model(
        model,
        generated.counts,
        covariates,
    )
    trace = handlers.trace(
        handlers.seed(program, random.PRNGKey(9))
    ).get_trace()

    assert f"sp.{process.name}.{process.coherence_parameter}" in trace
    assert f"sp.{process.name}.{process.sigma_parameter}" in trace
    assert "obs.records.sp" in trace
