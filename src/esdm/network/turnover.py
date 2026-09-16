"""Interaction-network turnover and rewiring diagnostics."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence

from .distribution import Edge, InteractionNetworkDistribution

_EMPTY = object()


def _entropy(probabilities) -> float:
    return -math.fsum(p * math.log(p) for p in probabilities if p > 0.0)


def _normalized_edge_distribution(network: InteractionNetworkDistribution):
    mass = network.edge_mass_distribution()
    if mass:
        return mass
    return {_EMPTY: 1.0}


def network_beta_q1(networks: Sequence[InteractionNetworkDistribution]) -> float:
    """Multiplicative q=1 beta diversity of normalized edge-mass distributions."""

    if len(networks) < 2:
        raise ValueError("at least two networks are required")

    distributions = [_normalized_edge_distribution(network) for network in networks]
    weight = 1.0 / len(distributions)
    pooled: dict[object, float] = defaultdict(float)
    within_entropies: list[float] = []

    for distribution in distributions:
        within_entropies.append(_entropy(distribution.values()))
        for edge, probability in distribution.items():
            pooled[edge] += weight * probability

    gamma_entropy = _entropy(pooled.values())
    alpha_entropy = math.fsum(within_entropies) / len(within_entropies)
    return math.exp(gamma_entropy - alpha_entropy)


def shared_taxon_rewiring_beta_q1(
    a: InteractionNetworkDistribution,
    b: InteractionNetworkDistribution,
) -> float:
    """Edge beta after conditioning on taxa shared by both communities."""

    shared = tuple(taxon for taxon in a.taxa if taxon in set(b.taxa))
    if len(shared) < 2:
        raise ValueError("at least two shared taxa are required for rewiring")
    return network_beta_q1((a.restrict_taxa(shared), b.restrict_taxa(shared)))


def state_conditioned_connectance(
    networks_by_state: Mapping[str, InteractionNetworkDistribution],
) -> dict[str, float]:
    """Report expected connectance separately for each declared state slice."""

    out: dict[str, float] = {}
    for state, network in networks_by_state.items():
        if not isinstance(state, str) or not state.strip():
            raise ValueError("state labels must be non-empty strings")
        out[state] = network.expected_connectance()
    return out
