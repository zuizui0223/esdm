import pytest

from esdm.network import (
    InteractionNetworkDistribution,
    interaction_diversity_q1,
    partner_diversity_q1,
)


def test_interaction_diversity_effective_edge_number():
    one = InteractionNetworkDistribution(
        taxa=("a", "b", "c"), edge_probabilities={("a", "b"): 0.9}
    )
    two = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.5, ("a", "c"): 0.5},
    )
    empty = InteractionNetworkDistribution(taxa=("a", "b"), edge_probabilities={})

    assert interaction_diversity_q1(one) == pytest.approx(1.0)
    assert interaction_diversity_q1(two) == pytest.approx(2.0)
    assert interaction_diversity_q1(empty) == 0.0


def test_partner_diversity_is_source_specific():
    net = InteractionNetworkDistribution(
        taxa=("a", "b", "c"),
        edge_probabilities={("a", "b"): 0.4, ("a", "c"): 0.4, ("b", "c"): 0.8},
    )
    assert partner_diversity_q1(net, "a") == pytest.approx(2.0)
    assert partner_diversity_q1(net, "b") == pytest.approx(1.0)
    assert partner_diversity_q1(net, "c") == 0.0
    with pytest.raises(ValueError):
        partner_diversity_q1(net, "missing")
