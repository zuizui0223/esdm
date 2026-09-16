"""q=1 state-resolved beta diversity decomposition."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections import defaultdict
from typing import Sequence

from esdm.core.community import CommunityStateDistribution
from .alpha import shannon_entropy


@dataclass(frozen=True, slots=True)
class BetaDiversityQ1:
    taxonomic: float
    state_given_taxon: float
    joint: float


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def beta_diversity_q1(communities: Sequence[CommunityStateDistribution]) -> BetaDiversityQ1:
    if len(communities) < 2:
        raise ValueError("at least two communities are required")

    pooled_taxa: dict[str, float] = defaultdict(float)
    pooled_joint: dict[tuple[str, str], float] = defaultdict(float)
    within_taxon_entropy: list[float] = []
    within_joint_entropy: list[float] = []
    weight = 1.0 / len(communities)

    for community in communities:
        for taxon, probability in community.taxon_weights.items():
            pooled_taxa[taxon] += weight * probability
        joint = community.joint_probabilities()
        for key, probability in joint.items():
            pooled_joint[key] += weight * probability
        within_taxon_entropy.append(shannon_entropy(community.taxon_weights.values()))
        within_joint_entropy.append(shannon_entropy(joint.values()))

    taxon_log_beta = shannon_entropy(pooled_taxa.values()) - _mean(within_taxon_entropy)
    joint_log_beta = shannon_entropy(pooled_joint.values()) - _mean(within_joint_entropy)

    taxonomic = math.exp(taxon_log_beta)
    joint = math.exp(joint_log_beta)
    state_given_taxon = joint / taxonomic
    return BetaDiversityQ1(
        taxonomic=taxonomic,
        state_given_taxon=state_given_taxon,
        joint=joint,
    )
