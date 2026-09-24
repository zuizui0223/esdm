import pytest

from esdm.authorization import InteractionEventRecord, authorize_interaction_event
from esdm.claims import EdgeClaimEvidence, authorize_biotic_edge_claim
from esdm.core import InteractionEvidenceTier


def _positive_event():
    return authorize_interaction_event(
        InteractionEventRecord("source", "focal", "event-1", "positive")
    )


def test_predictive_dependence_cannot_self_promote_to_realized():
    evidence = EdgeClaimEvidence(
        "source",
        "focal",
        InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
    )

    result = authorize_biotic_edge_claim(
        evidence,
        requested_tier=InteractionEvidenceTier.CAUSAL,
    )

    assert result.edge.tier is InteractionEvidenceTier.PREDICTIVE_DEPENDENCE
    assert result.maximum_authorized_tier is InteractionEvidenceTier.PREDICTIVE_DEPENDENCE
    assert result.capped is True


def test_authorized_positive_pair_event_unlocks_realized_but_not_functional():
    evidence = EdgeClaimEvidence(
        "source",
        "focal",
        InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
        event_observations=(_positive_event(),),
    )

    result = authorize_biotic_edge_claim(
        evidence,
        requested_tier=InteractionEvidenceTier.CAUSAL,
    )

    assert result.edge.tier is InteractionEvidenceTier.REALIZED
    assert result.maximum_authorized_tier is InteractionEvidenceTier.REALIZED


def test_missing_or_negative_event_does_not_unlock_realized():
    missing = authorize_interaction_event(
        InteractionEventRecord("source", "focal", "missing", "missing")
    )
    negative = authorize_interaction_event(
        InteractionEventRecord(
            "source",
            "focal",
            "negative",
            "negative",
            negative_gate_passed=True,
        )
    )
    evidence = EdgeClaimEvidence(
        "source",
        "focal",
        InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
        event_observations=(missing, negative),
    )

    result = authorize_biotic_edge_claim(
        evidence,
        requested_tier=InteractionEvidenceTier.REALIZED,
    )

    assert result.edge.tier is InteractionEvidenceTier.PREDICTIVE_DEPENDENCE


def test_functional_and_causal_tiers_require_explicit_extra_evidence():
    event = _positive_event()

    functional = authorize_biotic_edge_claim(
        EdgeClaimEvidence(
            "source",
            "focal",
            InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
            event_observations=(event,),
            functional_endpoint_supported=True,
        ),
        requested_tier=InteractionEvidenceTier.CAUSAL,
    )
    causal = authorize_biotic_edge_claim(
        EdgeClaimEvidence(
            "source",
            "focal",
            InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
            event_observations=(event,),
            functional_endpoint_supported=True,
            intervention_supported=True,
        ),
        requested_tier=InteractionEvidenceTier.CAUSAL,
    )

    assert functional.edge.tier is InteractionEvidenceTier.FUNCTIONAL
    assert causal.edge.tier is InteractionEvidenceTier.CAUSAL


def test_event_evidence_cannot_be_reused_for_wrong_edge():
    event = _positive_event()
    with pytest.raises(ValueError, match="must match"):
        EdgeClaimEvidence(
            "other",
            "focal",
            InteractionEvidenceTier.PREDICTIVE_DEPENDENCE,
            event_observations=(event,),
        )


def test_model_only_tier_above_predictive_is_rejected():
    with pytest.raises(ValueError, match="cannot exceed"):
        EdgeClaimEvidence(
            "source",
            "focal",
            InteractionEvidenceTier.REALIZED,
        )
