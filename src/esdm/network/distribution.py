"""Generic probability distribution over declared biotic interaction edges."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping
from types import MappingProxyType

Edge = tuple[str, str]


@dataclass(frozen=True, slots=True)
class InteractionNetworkDistribution:
    """Learner-agnostic distribution over directed interaction edges.

    Unspecified eligible edges have probability zero.  Probabilities describe
    the evidence tier supplied by the caller; they are never promoted to
    realized, functional, or causal interactions automatically.
    """

    taxa: tuple[str, ...]
    edge_probabilities: Mapping[Edge, float]
    allow_self_edges: bool = False

    def __post_init__(self) -> None:
        taxa = tuple(self.taxa)
        if not taxa:
            raise ValueError("taxa must contain at least one taxon")
        if any(not isinstance(taxon, str) or not taxon.strip() for taxon in taxa):
            raise ValueError("taxa must be non-empty strings")
        if len(set(taxa)) != len(taxa):
            raise ValueError("taxa must be unique")

        normalized: dict[Edge, float] = {}
        taxa_set = set(taxa)
        for edge, probability in self.edge_probabilities.items():
            if not isinstance(edge, tuple) or len(edge) != 2:
                raise ValueError("edge keys must be (source, target) tuples")
            source, target = edge
            if source not in taxa_set or target not in taxa_set:
                raise ValueError("edge endpoints must be declared taxa")
            if source == target and not self.allow_self_edges:
                raise ValueError("self edges are disabled")
            probability = float(probability)
            if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
                raise ValueError("edge probabilities must be finite values in [0, 1]")
            normalized[(source, target)] = probability

        object.__setattr__(self, "taxa", taxa)
        object.__setattr__(self, "edge_probabilities", MappingProxyType(normalized))

    @property
    def eligible_edges(self) -> tuple[Edge, ...]:
        return tuple(
            (source, target)
            for source in self.taxa
            for target in self.taxa
            if self.allow_self_edges or source != target
        )

    def edge_probability(self, source: str, target: str) -> float:
        if source not in self.taxa or target not in self.taxa:
            raise ValueError("edge endpoints must be declared taxa")
        if source == target and not self.allow_self_edges:
            raise ValueError("self edges are disabled")
        return self.edge_probabilities.get((source, target), 0.0)

    def expected_connectance(self) -> float:
        edges = self.eligible_edges
        if not edges:
            return 0.0
        return math.fsum(self.edge_probability(*edge) for edge in edges) / len(edges)

    def edge_mass_distribution(self) -> dict[Edge, float]:
        positive = {
            edge: self.edge_probability(*edge)
            for edge in self.eligible_edges
            if self.edge_probability(*edge) > 0.0
        }
        total = math.fsum(positive.values())
        if total <= 0.0:
            return {}
        return {edge: probability / total for edge, probability in positive.items()}

    def restrict_taxa(self, taxa: tuple[str, ...] | list[str]) -> "InteractionNetworkDistribution":
        requested = tuple(taxa)
        if any(taxon not in self.taxa for taxon in requested):
            raise ValueError("restricted taxa must be present in the source network")
        probabilities = {
            (source, target): probability
            for (source, target), probability in self.edge_probabilities.items()
            if source in requested and target in requested
        }
        return InteractionNetworkDistribution(
            taxa=requested,
            edge_probabilities=probabilities,
            allow_self_edges=self.allow_self_edges,
        )
