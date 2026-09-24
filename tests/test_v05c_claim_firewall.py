import pytest

from esdm.claims import ClaimStatus, bounded_interaction_claim
from esdm.core import InteractionEvidenceTier


def test_distribution_only_stops_at_predictive_dependence():
    claim = bounded_interaction_claim(
        "source->focal",
        distribution_supported=True,
        event_supported=False,
    )
    assert claim.status is ClaimStatus.SUPPORTED
    assert claim.tier is InteractionEvidenceTier.PREDICTIVE_DEPENDENCE


def test_event_endpoint_is_required_for_realized_tier():
    claim = bounded_interaction_claim(
        "source->focal",
        distribution_supported=True,
        event_supported=True,
    )
    assert claim.tier is InteractionEvidenceTier.REALIZED


def test_causal_tier_requires_realized_event_layer():
    with pytest.raises(ValueError, match="cannot skip"):
        bounded_interaction_claim(
            "source->focal",
            distribution_supported=True,
            event_supported=False,
            causal_supported=True,
        )

    claim = bounded_interaction_claim(
        "source->focal",
        distribution_supported=True,
        event_supported=True,
        causal_supported=True,
    )
    assert claim.tier is InteractionEvidenceTier.CAUSAL


def test_no_supported_endpoint_is_not_supported():
    claim = bounded_interaction_claim(
        "source->focal",
        distribution_supported=False,
        event_supported=False,
    )
    assert claim.status is ClaimStatus.NOT_SUPPORTED
    assert claim.tier is InteractionEvidenceTier.COAVAILABLE
