"""Posterior/downstream network summaries.

The existing deterministic network primitives are retained as summary operators. New
generative code should not construct these objects as ecological-process inputs.
"""

from esdm.network import (
    InteractionNetworkDistribution,
    interaction_diversity_q1,
    network_beta_q1,
    partner_diversity_q1,
    shared_taxon_rewiring_beta_q1,
    state_conditioned_connectance,
)

__all__ = [
    "InteractionNetworkDistribution",
    "interaction_diversity_q1",
    "network_beta_q1",
    "partner_diversity_q1",
    "shared_taxon_rewiring_beta_q1",
    "state_conditioned_connectance",
]
