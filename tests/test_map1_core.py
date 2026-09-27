import importlib.util
import math

import pytest

from esdm.process import ExchangeableMapField, FixedCoherenceMapField
from esdm.validate.map1_known_truth import (
    MODEL_IDS,
    WORLD_IDS,
    make_map1_fixture,
    make_map1_model,
    make_map1_worlds,
    map1_truth_theta,
)


JAX_AVAILABLE = importlib.util.find_spec("jax") is not None


def test_map1_processes_do_not_estimate_covariance_mechanism_axes():
    fixture = make_map1_fixture()
    coherent = FixedCoherenceMapField(fixture.graph)
    exchangeable = ExchangeableMapField(fixture.graph)

    coherent_priors = coherent.priors()
    exchangeable_priors = exchangeable.priors()

    for priors in (coherent_priors, exchangeable_priors):
        assert set(name for name in priors if "rho" in name) == set()
        assert set(name for name in priors if "gamma" in name) == set()
        assert set(name for name in priors if "beta" in name) == set()
        assert priors["map_sigma"].distribution == "HalfNormal"
        assert sum(name.startswith("map_z_") for name in priors) == fixture.graph.node_count - 1


def test_map1_coherent_and_exchangeable_fields_are_exact_zero_sum():
    fixture = make_map1_fixture()
    for process in (
        FixedCoherenceMapField(fixture.graph),
        ExchangeableMapField(fixture.graph),
    ):
        theta = {"map_sigma": 0.6}
        for index in range(fixture.graph.node_count - 1):
            theta[process.innovation_parameter(index)] = math.sin(index + 0.3)
        values = process.node_field(theta)
        assert math.fsum(values) == pytest.approx(0.0, abs=1e-10)
        assert any(abs(value) > 1e-8 for value in values)


def test_map1_fixed_coherence_is_not_exchangeable_flexibility():
    fixture = make_map1_fixture()
    coherent = FixedCoherenceMapField(fixture.graph)
    exchangeable = ExchangeableMapField(fixture.graph)
    theta = {"map_sigma": 0.55}
    for index in range(fixture.graph.node_count - 1):
        theta[f"map_z_{index:04d}"] = math.cos(0.5 + index)

    u_coherent = coherent.node_field(theta)
    u_exchangeable = exchangeable.node_field(theta)

    assert u_coherent != pytest.approx(u_exchangeable)


def test_map1_model_family_and_worlds_are_finite():
    fixture = make_map1_fixture()
    for model_id in MODEL_IDS:
        model = make_map1_model(fixture, model_id)
        model.check_design()
        truth = map1_truth_theta(fixture, model_id)
        expected = {
            parameter
            for process in model.species["sp"]
            for parameter in process.priors()
        }
        assert set(truth["sp"]) == expected

    worlds = make_map1_worlds()
    assert tuple(world.world_id for world in worlds) == WORLD_IDS
    assert tuple(world.truth_model_id for world in worlds) == MODEL_IDS


def test_map1_worlds_isolate_coherence_from_extra_latent_flexibility():
    worlds = {world.world_id: world for world in make_map1_worlds()}
    assert ("BC", "B0", "H1") in worlds["P1"].expected_positive_comparisons
    assert ("BC", "BX", "H1") in worlds["P1"].expected_positive_comparisons
    assert ("BC", "B0", "H1") in worlds["N0"].expected_null_comparisons
    assert ("BC", "BX", "H1") in worlds["N1"].expected_null_comparisons


def test_map1_latent_realization_is_fresh_but_hyperparameters_are_fixed():
    fixture = make_map1_fixture()
    first = map1_truth_theta(fixture, "BC", innovation_seed=10)["sp"]
    repeat = map1_truth_theta(fixture, "BC", innovation_seed=10)["sp"]
    second = map1_truth_theta(fixture, "BC", innovation_seed=11)["sp"]

    names = sorted(name for name in first if name.startswith("map_z_"))
    assert [first[name] for name in names] == [repeat[name] for name in names]
    assert [first[name] for name in names] != [second[name] for name in names]
    assert first["map_sigma"] == second["map_sigma"] == 0.55


@pytest.mark.skipif(not JAX_AVAILABLE, reason="JAX optional backend not installed")
def test_map1_coherent_field_is_differentiable_in_amplitude():
    import jax
    import jax.numpy as jnp

    fixture = make_map1_fixture()
    process = FixedCoherenceMapField(fixture.graph)

    innovations = {
        process.innovation_parameter(index): math.sin(index + 0.2)
        for index in range(fixture.graph.node_count - 1)
    }

    def objective(sigma):
        theta = {process.sigma_parameter: sigma, **innovations}
        field = process.node_field_array(theta, array_module=jnp)
        return jnp.sum(field * field)

    derivative = jax.grad(objective)(jnp.asarray(0.5))
    assert bool(jnp.isfinite(derivative))
    assert abs(float(derivative)) > 1e-8
