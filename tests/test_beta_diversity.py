import pytest

from esdm.core import CommunityStateDistribution
from esdm.diversity.beta import beta_diversity_q1


def test_beta_q1_separates_taxonomic_turnover_from_state_turnover():
    site_a = CommunityStateDistribution(
        taxon_weights={"a": 1.0},
        state_probabilities={"a": {"active": 1.0}},
    )
    site_b = CommunityStateDistribution(
        taxon_weights={"b": 1.0},
        state_probabilities={"b": {"active": 1.0}},
    )
    result = beta_diversity_q1([site_a, site_b])
    assert result.taxonomic == pytest.approx(2.0)
    assert result.state_given_taxon == pytest.approx(1.0)
    assert result.joint == pytest.approx(2.0)


def test_beta_q1_detects_state_turnover_without_taxonomic_turnover():
    site_early = CommunityStateDistribution(
        taxon_weights={"a": 0.5, "b": 0.5},
        state_probabilities={
            "a": {"early": 1.0},
            "b": {"early": 1.0},
        },
    )
    site_late = CommunityStateDistribution(
        taxon_weights={"a": 0.5, "b": 0.5},
        state_probabilities={
            "a": {"late": 1.0},
            "b": {"late": 1.0},
        },
    )
    result = beta_diversity_q1([site_early, site_late])
    assert result.taxonomic == pytest.approx(1.0)
    assert result.state_given_taxon == pytest.approx(2.0)
    assert result.joint == pytest.approx(2.0)
    assert result.joint == pytest.approx(result.taxonomic * result.state_given_taxon)
