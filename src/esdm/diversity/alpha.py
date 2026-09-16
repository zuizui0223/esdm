"""q=1 state-resolved alpha diversity decomposition."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from esdm.core.community import CommunityStateDistribution


def _validated_probabilities(probabilities: Iterable[float]) -> list[float]:
    values = [float(value) for value in probabilities]
    if not values:
        raise ValueError("probability vector must not be empty")
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise ValueError("probabilities must be finite and non-negative")
    total = sum(values)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("probabilities must sum to one")
    return values


def shannon_entropy(probabilities: Iterable[float]) -> float:
    values = _validated_probabilities(probabilities)
    return -sum(value * math.log(value) for value in values if value > 0.0)


def hill_q1(probabilities: Iterable[float]) -> float:
    return math.exp(shannon_entropy(probabilities))


@dataclass(frozen=True, slots=True)
class AlphaDiversityQ1:
    taxonomic: float
    state_given_taxon: float
    joint: float


def alpha_diversity_q1(community: CommunityStateDistribution) -> AlphaDiversityQ1:
    taxonomic_entropy = shannon_entropy(community.taxon_weights.values())
    conditional_state_entropy = 0.0
    for taxon, taxon_weight in community.taxon_weights.items():
        conditional_state_entropy += taxon_weight * shannon_entropy(
            community.state_probabilities[taxon].values()
        )

    taxonomic = math.exp(taxonomic_entropy)
    state_given_taxon = math.exp(conditional_state_entropy)
    joint = math.exp(taxonomic_entropy + conditional_state_entropy)
    return AlphaDiversityQ1(
        taxonomic=taxonomic,
        state_given_taxon=state_given_taxon,
        joint=joint,
    )
