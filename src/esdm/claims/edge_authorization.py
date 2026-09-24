"""Fail-closed evidence-tier authorization for directed biotic edges."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.authorization import AuthorizedInteractionEvent
from esdm.core import BioticEdge, InteractionEvidenceTier


@dataclass(frozen=True, slots=True)
class EdgeClaimEvidence:
    """Evidence available for one directed source-to-target edge.

    model_tier is the strongest tier supported without pair-specific event evidence
    and is therefore capped at PREDICTIVE_DEPENDENCE.
    """

    source: str
    target: str
    model_tier: InteractionEvidenceTier
    event_observations: tuple[AuthorizedInteractionEvent, ...] = ()
    functional_endpoint_supported: bool = False
    intervention_supported: bool = False

    def __post_init__(self) -> None:
        source = str(self.source).strip()
        target = str(self.target).strip()
        if not source or not target or source == target:
            raise ValueError("edge source/target must be distinct non-empty strings")
        if not isinstance(self.model_tier, InteractionEvidenceTier):
            raise TypeError("model_tier must be an InteractionEvidenceTier")
        if self.model_tier > InteractionEvidenceTier.PREDICTIVE_DEPENDENCE:
            raise ValueError(
                "model-only evidence cannot exceed PREDICTIVE_DEPENDENCE"
            )
        events = tuple(self.event_observations)
        for event in events:
            if not isinstance(event, AuthorizedInteractionEvent):
                raise TypeError(
                    "event_observations must contain AuthorizedInteractionEvent values"
                )
            if event.source != source or event.target != target:
                raise ValueError(
                    "event evidence must match the authorized edge source and target"
                )
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "event_observations", events)


@dataclass(frozen=True, slots=True)
class EdgeClaimAuthorization:
    edge: BioticEdge
    requested_tier: InteractionEvidenceTier
    maximum_authorized_tier: InteractionEvidenceTier
    reasons: tuple[str, ...]

    @property
    def capped(self) -> bool:
        return self.edge.tier < self.requested_tier


def maximum_authorized_edge_tier(
    evidence: EdgeClaimEvidence,
) -> tuple[InteractionEvidenceTier, tuple[str, ...]]:
    """Return the strongest tier authorized by independent evidence."""

    reasons = [f"model_tier={evidence.model_tier.name}"]
    maximum = evidence.model_tier

    positive_events = tuple(
        event for event in evidence.event_observations if event.is_positive
    )
    authorized_negatives = tuple(
        event for event in evidence.event_observations if event.is_negative
    )
    unavailable = tuple(
        event
        for event in evidence.event_observations
        if not event.is_positive and not event.is_negative
    )

    if positive_events:
        maximum = max(maximum, InteractionEvidenceTier.REALIZED)
        reasons.append(f"authorized_positive_events={len(positive_events)}")
    else:
        reasons.append("authorized_positive_events=0")

    if authorized_negatives:
        reasons.append(f"authorized_negative_events={len(authorized_negatives)}")
    if unavailable:
        reasons.append(f"unavailable_event_records={len(unavailable)}")

    if evidence.functional_endpoint_supported and positive_events:
        maximum = max(maximum, InteractionEvidenceTier.FUNCTIONAL)
        reasons.append("functional_endpoint_supported=true")
    elif evidence.functional_endpoint_supported:
        reasons.append("functional_endpoint_blocked_without_realized_event")

    if (
        evidence.intervention_supported
        and evidence.functional_endpoint_supported
        and positive_events
    ):
        maximum = InteractionEvidenceTier.CAUSAL
        reasons.append("intervention_supported=true")
    elif evidence.intervention_supported:
        reasons.append("causal_promotion_blocked_by_missing_prerequisites")

    return maximum, tuple(reasons)


def authorize_biotic_edge_claim(
    evidence: EdgeClaimEvidence,
    *,
    requested_tier: InteractionEvidenceTier,
    interaction_type: str | None = None,
) -> EdgeClaimAuthorization:
    """Cap a requested edge claim at the strongest independently authorized tier."""

    if not isinstance(requested_tier, InteractionEvidenceTier):
        raise TypeError("requested_tier must be an InteractionEvidenceTier")

    maximum, reasons = maximum_authorized_edge_tier(evidence)
    authorized = min(requested_tier, maximum)
    metadata = {
        "requested_tier": requested_tier.name,
        "maximum_authorized_tier": maximum.name,
        "event_evidence_required_for_realized": True,
    }
    edge = BioticEdge(
        evidence.source,
        evidence.target,
        authorized,
        interaction_type=interaction_type,
        metadata=metadata,
    )
    if authorized < requested_tier:
        reasons = (*reasons, f"claim_capped_at={authorized.name}")
    return EdgeClaimAuthorization(
        edge=edge,
        requested_tier=requested_tier,
        maximum_authorized_tier=maximum,
        reasons=tuple(reasons),
    )
