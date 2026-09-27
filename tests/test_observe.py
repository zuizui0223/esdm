from esdm.observe import ObservationCandidate, nominate_discriminating_observations
from esdm.worlds import EcologicalWorld, EcologicalWorldSet


def make_worlds():
    return EcologicalWorldSet(
        (
            EcologicalWorld("competition", {}),
            EcologicalWorld("mutualism", {}),
        )
    )


def test_only_world_discriminating_candidates_are_admitted():
    worlds = make_worlds()
    candidates = (
        ObservationCandidate(
            "fitness_response",
            {"competition": "negative", "mutualism": "positive"},
        ),
        ObservationCandidate(
            "cooccurrence",
            {"competition": "positive", "mutualism": "positive"},
        ),
        ObservationCandidate(
            "partial",
            {"competition": "negative"},
        ),
    )
    result = nominate_discriminating_observations(worlds, candidates)
    assert result.candidate_ids == ("fitness_response",)
    assert result.ranked is False
    assert result.claim == "discriminating_candidate_set"


def test_output_order_is_deterministic_but_not_scientific_ranking():
    worlds = make_worlds()
    candidates = (
        ObservationCandidate("z_candidate", {"competition": "negative", "mutualism": "positive"}),
        ObservationCandidate("a_candidate", {"competition": "positive", "mutualism": "negative"}),
    )
    result = nominate_discriminating_observations(worlds, candidates)
    assert result.candidate_ids == ("a_candidate", "z_candidate")
    assert result.ranked is False
    assert not hasattr(result, "scores")
    assert not hasattr(result, "occupancy")


def test_candidate_with_partial_predictions_is_admitted_if_declared_worlds_conflict():
    worlds = EcologicalWorldSet(
        (
            EcologicalWorld("w1", {}),
            EcologicalWorld("w2", {}),
            EcologicalWorld("w3", {}),
        )
    )
    candidate = ObservationCandidate(
        "partial_but_discriminating",
        {"w1": "positive", "w2": "negative"},
    )
    result = nominate_discriminating_observations(worlds, (candidate,))
    assert result.candidate_ids == ("partial_but_discriminating",)


def test_one_surviving_world_has_no_discriminating_candidate():
    worlds = EcologicalWorldSet((EcologicalWorld("only", {}),))
    candidate = ObservationCandidate("obs", {"only": "positive"})
    result = nominate_discriminating_observations(worlds, (candidate,))
    assert result.candidate_ids == ()
