import pytest

from esdm.core import CommunityStateDistribution
from esdm.diversity.alpha import alpha_diversity_q1, hill_q1


def test_alpha_q1_reduces_to_taxonomic_diversity_for_deterministic_states():
    community = CommunityStateDistribution(
        taxon_weights={"a": 0.5, "b": 0.5},
        state_probabilities={
            "a": {"active": 1.0},
            "b": {"active": 1.0},
        },
    )
    result = alpha_diversity_q1(community)
    assert result.taxonomic == pytest.approx(2.0)
    assert result.state_given_taxon == pytest.approx(1.0)
    assert result.joint == pytest.approx(2.0)


def test_alpha_q1_multiplies_taxon_and_within_taxon_state_diversity():
    community = CommunityStateDistribution(
        taxon_weights={"a": 0.5, "b": 0.5},
        state_probabilities={
            "a": {"early": 0.5, "late": 0.5},
            "b": {"early": 0.5, "late": 0.5},
        },
    )
    result = alpha_diversity_q1(community)
    assert result.taxonomic == pytest.approx(2.0)
    assert result.state_given_taxon == pytest.approx(2.0)
    assert result.joint == pytest.approx(4.0)
    assert result.joint == pytest.approx(
        hill_q1(community.joint_probabilities().values())
    )
