"""Typed scientific claim states separated from evidence tier."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from esdm.core import InteractionEvidenceTier


class ClaimStatus(str, Enum):
    DESIGN_UNINFORMED = "DesignUninformed"
    UNTESTED = "Untested"
    NOT_IDENTIFIED = "NotIdentified"
    NOT_SUPPORTED = "NotSupported"
    SUPPORTED = "Supported"


@dataclass(frozen=True, slots=True)
class Claim:
    status: ClaimStatus
    tier: InteractionEvidenceTier
    target: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        target = str(self.target).strip()
        if not target:
            raise ValueError("claim target must be non-empty")
        if not isinstance(self.status, ClaimStatus):
            raise TypeError("status must be a ClaimStatus")
        if not isinstance(self.tier, InteractionEvidenceTier):
            raise TypeError("tier must be an InteractionEvidenceTier")
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "evidence", tuple(str(x) for x in self.evidence))
