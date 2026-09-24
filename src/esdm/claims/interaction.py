"""Bounded interaction-claim promotion from independent evidence channels."""

from __future__ import annotations

from esdm.core import InteractionEvidenceTier
from .types import Claim, ClaimStatus


def bounded_interaction_claim(
    target: str,
    *,
    distribution_supported: bool,
    event_supported: bool,
    causal_supported: bool = False,
) -> Claim:
    """Promote interaction evidence without skipping required endpoint layers.

    Distributional partner effects can establish at most predictive dependence.
    A directly observed interaction-event endpoint is required for REALIZED evidence.
    CAUSAL additionally requires an explicitly separate causal design flag.
    """

    if causal_supported and not event_supported:
        raise ValueError(
            "causal interaction evidence cannot skip the realized-event layer"
        )

    evidence = []
    if distribution_supported:
        evidence.append("distributional_partner_effect_supported")
    if event_supported:
        evidence.append("independent_interaction_event_supported")
    if causal_supported:
        evidence.append("independent_causal_design_supported")

    if causal_supported:
        tier = InteractionEvidenceTier.CAUSAL
    elif event_supported:
        tier = InteractionEvidenceTier.REALIZED
    elif distribution_supported:
        tier = InteractionEvidenceTier.PREDICTIVE_DEPENDENCE
    else:
        tier = InteractionEvidenceTier.COAVAILABLE

    status = (
        ClaimStatus.SUPPORTED
        if distribution_supported or event_supported or causal_supported
        else ClaimStatus.NOT_SUPPORTED
    )
    return Claim(
        status=status,
        tier=tier,
        target=target,
        evidence=tuple(evidence),
    )
