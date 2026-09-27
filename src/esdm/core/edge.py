"""Generic biotic-edge evidence semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Mapping, Any


class InteractionEvidenceTier(IntEnum):
    """Evidence depth for a generic biotic edge.

    The ordering is epistemic, not taxonomic. No interaction type is inferred
    from node identity.
    """

    COAVAILABLE = 0
    STATE_COMPATIBLE = 1
    PREDICTIVE_DEPENDENCE = 2
    REALIZED = 3
    FUNCTIONAL = 4
    CAUSAL = 5


@dataclass(frozen=True, slots=True)
class BioticEdge:
    source: str
    target: str
    tier: InteractionEvidenceTier
    interaction_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError("target must be a non-empty string")
        if not isinstance(self.tier, InteractionEvidenceTier):
            raise TypeError("tier must be an InteractionEvidenceTier")
        if self.interaction_type is not None:
            if not isinstance(self.interaction_type, str) or not self.interaction_type.strip():
                raise ValueError("interaction_type must be None or a non-empty string")
        object.__setattr__(self, "metadata", dict(self.metadata))
