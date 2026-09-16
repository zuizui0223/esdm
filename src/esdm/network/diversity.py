"""Interaction-network diversity summaries."""

from __future__ import annotations

import math

from .distribution import InteractionNetworkDistribution


def _effective_number_q1(weights) -> float:
    positive = [float(value) for value in weights if float(value) > 0.0]
    if not positive:
        return 0.0
    total = math.fsum(positive)
    normalized = [value / total for value in positive]
    entropy = -math.fsum(value * math.log(value) for value in normalized)
    return math.exp(entropy)


def interaction_diversity_q1(network: InteractionNetworkDistribution) -> float:
    """Effective number of interaction edges from normalized edge mass."""

    return _effective_number_q1(network.edge_mass_distribution().values())


def partner_diversity_q1(network: InteractionNetworkDistribution, source: str) -> float:
    """Effective number of outgoing partners for one declared source taxon."""

    if source not in network.taxa:
        raise ValueError("source must be a declared taxon")
    outgoing = [
        network.edge_probability(source, target)
        for target in network.taxa
        if network.allow_self_edges or target != source
    ]
    return _effective_number_q1(outgoing)
