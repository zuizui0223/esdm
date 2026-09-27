import math
import pytest

from esdm.network import InteractionNetworkDistribution


def test_network_declares_complete_nonself_edge_universe_and_connectance():
    net = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.8, ("a", "c"): 0.2},
    )
    assert len(net.eligible_edges) == 6
    assert net.edge_probability("a", "b") == pytest.approx(0.8)
    assert net.edge_probability("b", "a") == pytest.approx(0.0)
    assert net.expected_connectance() == pytest.approx(1.0 / 6.0)

    mass = net.edge_mass_distribution()
    assert math.fsum(mass.values()) == pytest.approx(1.0)
    assert mass[("a", "b")] == pytest.approx(0.8)
    assert mass[("a", "c")] == pytest.approx(0.2)


def test_empty_network_has_zero_edge_mass_distribution():
    net = InteractionNetworkDistribution(taxa=("a", "b"), edge_probabilities={})
    assert net.expected_connectance() == 0.0
    assert net.edge_mass_distribution() == {}


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf")])
def test_network_rejects_invalid_edge_probabilities(value):
    with pytest.raises(ValueError):
        InteractionNetworkDistribution(
            taxa=("a", "b"), edge_probabilities={("a", "b"): value}
        )


def test_network_rejects_unknown_taxa_duplicate_taxa_and_self_edges():
    with pytest.raises(ValueError):
        InteractionNetworkDistribution(
            taxa=("a", "b"), edge_probabilities={("a", "c"): 0.5}
        )
    with pytest.raises(ValueError):
        InteractionNetworkDistribution(taxa=("a", "a"), edge_probabilities={})
    with pytest.raises(ValueError):
        InteractionNetworkDistribution(
            taxa=("a", "b"), edge_probabilities={("a", "a"): 0.5}
        )


def test_self_edges_can_be_declared_explicitly():
    net = InteractionNetworkDistribution(
        taxa=("a", "b"),
        edge_probabilities={("a", "a"): 0.4},
        allow_self_edges=True,
    )
    assert len(net.eligible_edges) == 4
    assert net.edge_probability("a", "a") == pytest.approx(0.4)
