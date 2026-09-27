from esdm.authorization import ObservationRecord, authorize_observation
from esdm.worlds import EcologicalWorld, EcologicalWorldSet, contract_world_set


def make_worlds():
    shared = EcologicalWorld(
        "shared_environment",
        {
            "edge_presence": "negative",
            "fitness_response": "negative",
        },
    )
    competition = EcologicalWorld(
        "competition",
        {
            "edge_presence": "positive",
            "fitness_response": "negative",
        },
    )
    mutualism = EcologicalWorld(
        "mutualism",
        {
            "edge_presence": "positive",
            "fitness_response": "positive",
        },
    )
    return EcologicalWorldSet((shared, competition, mutualism))


def test_unavailable_evidence_eliminates_no_world():
    worlds = make_worlds()
    unavailable = authorize_observation(
        ObservationRecord("edge_presence", "negative", negative_gate_passed=False)
    )
    result = contract_world_set(worlds, (unavailable,))
    assert result.after.surviving_world_ids == worlds.surviving_world_ids
    assert result.eliminated_world_ids == ()
    assert result.ignored_observation_ids == ("edge_presence",)


def test_authorized_positive_eliminates_conflicting_declared_world():
    worlds = make_worlds()
    positive = authorize_observation(
        ObservationRecord("edge_presence", "positive", negative_gate_passed=False)
    )
    result = contract_world_set(worlds, (positive,))
    assert result.after.surviving_world_ids == ("competition", "mutualism")
    assert result.eliminated_world_ids == ("shared_environment",)


def test_authorized_negative_can_eliminate_positive_worlds():
    worlds = make_worlds()
    negative = authorize_observation(
        ObservationRecord("edge_presence", "negative", negative_gate_passed=True)
    )
    result = contract_world_set(worlds, (negative,))
    assert result.after.surviving_world_ids == ("shared_environment",)
    assert result.after.identifiable_within_declared_universe is True
    assert not hasattr(result.after, "truth")


def test_missing_world_prediction_does_not_force_elimination():
    silent = EcologicalWorld("silent", {})
    declaring = EcologicalWorld("declaring", {"obs": "negative"})
    worlds = EcologicalWorldSet((silent, declaring))
    positive = authorize_observation(
        ObservationRecord("obs", "positive", negative_gate_passed=False)
    )
    result = contract_world_set(worlds, (positive,))
    assert result.after.surviving_world_ids == ("silent",)


def test_sequential_contraction_is_monotone_and_never_readds_worlds():
    worlds = make_worlds()
    edge_positive = authorize_observation(
        ObservationRecord("edge_presence", "positive", negative_gate_passed=False)
    )
    first = contract_world_set(worlds, (edge_positive,))
    fitness_positive = authorize_observation(
        ObservationRecord("fitness_response", "positive", negative_gate_passed=False)
    )
    second = contract_world_set(first.after, (fitness_positive,))
    assert set(second.after.surviving_world_ids).issubset(first.after.surviving_world_ids)
    assert second.after.surviving_world_ids == ("mutualism",)
    assert second.after.identifiable_within_declared_universe is True
