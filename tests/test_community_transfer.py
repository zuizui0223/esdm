import math
import pytest

from esdm.transfer import (
    HeldoutCommunityPrediction,
    community_information_ceiling,
    community_log_score_gain,
)


def _mean_log_score(outcomes, probabilities):
    total = 0.0
    for y, p in zip(outcomes, probabilities, strict=True):
        total += math.log(p if y else 1.0 - p)
    return total / len(outcomes)


def test_community_gain_macro_averages_independent_communities():
    small = HeldoutCommunityPrediction(
        community_id="small",
        outcomes=(1,),
        baseline_probabilities=(0.5,),
        enriched_probabilities=(0.9,),
    )
    large = HeldoutCommunityPrediction(
        community_id="large",
        outcomes=(1, 1, 1),
        baseline_probabilities=(0.8, 0.8, 0.8),
        enriched_probabilities=(0.7, 0.7, 0.7),
    )
    result = community_log_score_gain((small, large))
    small_gain = _mean_log_score(small.outcomes, small.enriched_probabilities) - _mean_log_score(
        small.outcomes, small.baseline_probabilities
    )
    large_gain = _mean_log_score(large.outcomes, large.enriched_probabilities) - _mean_log_score(
        large.outcomes, large.baseline_probabilities
    )
    assert result.n_communities == 2
    assert result.per_community["small"] == pytest.approx(small_gain)
    assert result.per_community["large"] == pytest.approx(large_gain)
    assert result.macro_gain == pytest.approx((small_gain + large_gain) / 2.0)


def test_community_gain_positive_and_null_cases():
    positive = HeldoutCommunityPrediction(
        community_id="c1",
        outcomes=(1, 0),
        baseline_probabilities=(0.6, 0.4),
        enriched_probabilities=(0.9, 0.1),
    )
    null = HeldoutCommunityPrediction(
        community_id="c2",
        outcomes=(1, 0),
        baseline_probabilities=(0.7, 0.3),
        enriched_probabilities=(0.7, 0.3),
    )
    assert community_log_score_gain((positive,)).macro_gain > 0.0
    assert community_log_score_gain((null,)).macro_gain == pytest.approx(0.0)


def test_community_information_ceiling_is_non_skippable():
    state = community_log_score_gain(
        (
            HeldoutCommunityPrediction(
                community_id="c1",
                outcomes=(1,),
                baseline_probabilities=(0.5,),
                enriched_probabilities=(0.8,),
            ),
        )
    )
    interaction_fail = community_log_score_gain(
        (
            HeldoutCommunityPrediction(
                community_id="c1",
                outcomes=(1,),
                baseline_probabilities=(0.8,),
                enriched_probabilities=(0.7,),
            ),
        )
    )
    later_positive = community_log_score_gain(
        (
            HeldoutCommunityPrediction(
                community_id="c1",
                outcomes=(1,),
                baseline_probabilities=(0.7,),
                enriched_probabilities=(0.95,),
            ),
        )
    )
    ceiling = community_information_ceiling(
        base_level="abiotic",
        ordered_steps=(("state", "state"), ("interaction", "interaction"), ("function", "function")),
        gains_by_step={
            "state": state,
            "interaction": interaction_fail,
            "function": later_positive,
        },
    )
    assert ceiling.level == "state"
    assert [step.status for step in ceiling.steps] == ["pass", "fail", "not_reached"]


def test_heldout_prediction_validates_shapes_outcomes_and_probabilities():
    with pytest.raises(ValueError):
        HeldoutCommunityPrediction("c", (1,), (0.5, 0.5), (0.6,))
    with pytest.raises(ValueError):
        HeldoutCommunityPrediction("c", (2,), (0.5,), (0.6,))
    with pytest.raises(ValueError):
        HeldoutCommunityPrediction("c", (1,), (0.5,), (1.2,))
