import math

import pytest

from esdm.core import CommunityStateDistribution, StateAxis


def test_state_axis_accepts_unique_nonempty_states():
    axis = StateAxis("activity", ("inactive", "active"))
    assert axis.name == "activity"
    assert axis.states == ("inactive", "active")


def test_state_axis_rejects_duplicate_states():
    with pytest.raises(ValueError, match="unique"):
        StateAxis("activity", ("active", "active"))


def test_state_axis_rejects_blank_labels():
    with pytest.raises(ValueError):
        StateAxis("", ("inactive", "active"))
    with pytest.raises(ValueError):
        StateAxis("activity", ("inactive", ""))


def test_joint_distribution_multiplies_taxon_and_conditional_state_probabilities():
    community = CommunityStateDistribution(
        taxon_weights={"a": 0.25, "b": 0.75},
        state_probabilities={
            "a": {"low": 0.4, "high": 0.6},
            "b": {"low": 0.2, "high": 0.8},
        },
    )
    joint = community.joint_probabilities()
    assert joint[("a", "low")] == pytest.approx(0.10)
    assert joint[("a", "high")] == pytest.approx(0.15)
    assert joint[("b", "low")] == pytest.approx(0.15)
    assert joint[("b", "high")] == pytest.approx(0.60)
    assert sum(joint.values()) == pytest.approx(1.0)


def test_community_rejects_mismatched_taxa():
    with pytest.raises(ValueError, match="taxon"):
        CommunityStateDistribution(
            taxon_weights={"a": 1.0},
            state_probabilities={"b": {"present": 1.0}},
        )


@pytest.mark.parametrize(
    "weights",
    [
        {"a": 0.6, "b": 0.6},
        {"a": -0.1, "b": 1.1},
        {"a": math.inf},
    ],
)
def test_community_rejects_invalid_taxon_weights(weights):
    state_probabilities = {taxon: {"present": 1.0} for taxon in weights}
    with pytest.raises(ValueError):
        CommunityStateDistribution(
            taxon_weights=weights,
            state_probabilities=state_probabilities,
        )


def test_community_rejects_invalid_conditional_state_probabilities():
    with pytest.raises(ValueError):
        CommunityStateDistribution(
            taxon_weights={"a": 1.0},
            state_probabilities={"a": {"low": 0.2, "high": 0.2}},
        )
