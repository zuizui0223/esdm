import pytest

from esdm.benchmarks.worlds import (
    directed_biotic_coupling_world,
    hidden_shared_driver_world,
    observed_shared_environment_world,
    oracle_biotic_information_gain,
)


def test_observed_shared_environment_has_zero_conditional_biotic_gain():
    world = observed_shared_environment_world()
    assert world.interaction_truth is False
    assert abs(oracle_biotic_information_gain(world)) < 1e-12


def test_hidden_shared_driver_can_create_predictive_dependence_without_interaction():
    world = hidden_shared_driver_world()
    gain = oracle_biotic_information_gain(world)
    assert world.interaction_truth is False
    assert gain > 0.0


def test_directed_biotic_coupling_has_positive_conditional_gain():
    world = directed_biotic_coupling_world()
    gain = oracle_biotic_information_gain(world)
    assert world.interaction_truth is True
    assert gain > 0.0


def test_all_known_truth_worlds_are_normalized():
    for world in (
        observed_shared_environment_world(),
        hidden_shared_driver_world(),
        directed_biotic_coupling_world(),
    ):
        assert sum(world.joint.values()) == pytest.approx(1.0)
