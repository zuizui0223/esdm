"""Deterministic known-truth community-network benchmark worlds."""

from __future__ import annotations

from esdm.network import InteractionNetworkDistribution
from esdm.transfer import HeldoutCommunityPrediction


def stable_network_world() -> tuple[InteractionNetworkDistribution, InteractionNetworkDistribution]:
    probabilities = {("a", "b"): 0.7, ("b", "c"): 0.3}
    return (
        InteractionNetworkDistribution(("a", "b", "c"), probabilities),
        InteractionNetworkDistribution(("a", "b", "c"), probabilities),
    )


def pure_rewiring_world() -> tuple[InteractionNetworkDistribution, InteractionNetworkDistribution]:
    return (
        InteractionNetworkDistribution(
            ("a", "b", "c"), {("a", "b"): 1.0, ("b", "c"): 1.0}
        ),
        InteractionNetworkDistribution(
            ("a", "b", "c"), {("a", "c"): 1.0, ("b", "a"): 1.0}
        ),
    )


def connectance_shift_world() -> tuple[InteractionNetworkDistribution, InteractionNetworkDistribution]:
    return (
        InteractionNetworkDistribution(
            ("a", "b", "c"), {("a", "b"): 0.8, ("b", "c"): 0.4}
        ),
        InteractionNetworkDistribution(
            ("a", "b", "c"), {("a", "b"): 0.4, ("b", "c"): 0.2}
        ),
    )


def taxon_turnover_network_world() -> tuple[InteractionNetworkDistribution, InteractionNetworkDistribution]:
    return (
        InteractionNetworkDistribution(
            ("a", "b", "c"), {("b", "c"): 0.6, ("a", "b"): 0.8}
        ),
        InteractionNetworkDistribution(
            ("b", "c", "d"), {("b", "c"): 0.6, ("d", "c"): 0.8}
        ),
    )


def transfer_positive_network_world() -> tuple[HeldoutCommunityPrediction, ...]:
    return (
        HeldoutCommunityPrediction(
            community_id="community_1",
            outcomes=(1, 0, 1, 0),
            baseline_probabilities=(0.6, 0.4, 0.6, 0.4),
            enriched_probabilities=(0.85, 0.15, 0.85, 0.15),
        ),
        HeldoutCommunityPrediction(
            community_id="community_2",
            outcomes=(0, 1),
            baseline_probabilities=(0.4, 0.6),
            enriched_probabilities=(0.15, 0.85),
        ),
    )


def transfer_null_network_world() -> tuple[HeldoutCommunityPrediction, ...]:
    return (
        HeldoutCommunityPrediction(
            community_id="community_1",
            outcomes=(1, 0, 1, 0),
            baseline_probabilities=(0.7, 0.3, 0.7, 0.3),
            enriched_probabilities=(0.7, 0.3, 0.7, 0.3),
        ),
        HeldoutCommunityPrediction(
            community_id="community_2",
            outcomes=(0, 1),
            baseline_probabilities=(0.3, 0.7),
            enriched_probabilities=(0.3, 0.7),
        ),
    )
