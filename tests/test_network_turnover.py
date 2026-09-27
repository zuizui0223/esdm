import pytest

from esdm.network import (
    InteractionNetworkDistribution,
    network_beta_q1,
    shared_taxon_rewiring_beta_q1,
    state_conditioned_connectance,
)


def test_stable_network_has_beta_one():
    a = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.7, ("b", "c"): 0.3},
    )
    b = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.7, ("b", "c"): 0.3},
    )
    assert network_beta_q1((a, b)) == pytest.approx(1.0)
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_pure_rewiring_is_detected_with_unchanged_taxa():
    a = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 1.0, ("b", "c"): 1.0},
    )
    b = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "c"): 1.0, ("b", "a"): 1.0},
    )
    assert network_beta_q1((a, b)) == pytest.approx(2.0)
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(2.0)


def test_scalar_connectance_shift_is_not_rewiring():
    a = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.8, ("b", "c"): 0.4},
    )
    b = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.4, ("b", "c"): 0.2},
    )
    assert a.expected_connectance() != pytest.approx(b.expected_connectance())
    assert network_beta_q1((a, b)) == pytest.approx(1.0)
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_shared_taxon_rewiring_conditions_out_unique_taxa():
    a = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("b", "c"): 0.8, ("a", "b"): 0.9},
    )
    b = InteractionNetworkDistribution(
        taxa=("b", "c", "d"),
        edge_probabilities={("b", "c"): 0.8, ("d", "c"): 0.9},
    )
    assert network_beta_q1((a, b)) > 1.0
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_state_conditioned_connectance_reports_each_declared_state():
    resting = InteractionNetworkDistribution(
        taxa=("a", "b"), edge_probabilities={("a", "b"): 0.2}
    )
    active = InteractionNetworkDistribution(
        taxa=("a", "b"), edge_probabilities={("a", "b"): 0.8}
    )
    out = state_conditioned_connectance({"resting": resting, "active": active})
    assert out == pytest.approx({"resting": 0.1, "active": 0.4})
