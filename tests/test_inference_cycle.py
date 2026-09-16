from esdm.authorization import ObservationRecord
from esdm.inference import run_inference_observation_cycle
from esdm.observe import ObservationCandidate
from esdm.process import ProcessSupportSet, SeparatorEvidence
from esdm.worlds import EcologicalWorld, EcologicalWorldSet


def test_cycle_preserves_unavailable_negative_and_nominates_next_discriminator():
    raw_observations = (
        ObservationRecord("edge_absence", "negative", negative_gate_passed=False),
        ObservationRecord("edge_presence", "positive", negative_gate_passed=False),
    )

    process_support = ProcessSupportSet(
        ("shared_environment", "competition", "mutualism")
    )
    separator_evidence = (
        SeparatorEvidence(
            "shared_environment",
            "independent_field",
            "exclude",
            True,
            True,
            True,
        ),
        SeparatorEvidence(
            "competition",
            "independent_field",
            "compatible",
            True,
            True,
            True,
        ),
        SeparatorEvidence(
            "mutualism",
            "independent_field",
            "compatible",
            True,
            True,
            True,
        ),
    )

    worlds = EcologicalWorldSet(
        (
            EcologicalWorld(
                "shared_environment",
                {"edge_absence": "negative", "edge_presence": "negative"},
            ),
            EcologicalWorld(
                "competition",
                {"edge_absence": "positive", "edge_presence": "positive"},
            ),
            EcologicalWorld(
                "mutualism",
                {"edge_absence": "positive", "edge_presence": "positive"},
            ),
        )
    )

    candidates = (
        ObservationCandidate(
            "fitness_response",
            {"competition": "negative", "mutualism": "positive"},
        ),
        ObservationCandidate(
            "cooccurrence",
            {"competition": "positive", "mutualism": "positive"},
        ),
    )

    result = run_inference_observation_cycle(
        raw_observations=raw_observations,
        process_support=process_support,
        separator_evidence=separator_evidence,
        required_separator_ids=("independent_field",),
        world_set=worlds,
        observation_candidates=candidates,
    )

    assert tuple(obs.evidence_state for obs in result.authorized_observations) == (
        "unavailable",
        "positive",
    )
    assert result.process_refinement.refined.members == ("competition", "mutualism")
    assert result.world_contraction.after.surviving_world_ids == (
        "competition",
        "mutualism",
    )
    assert result.world_contraction.ignored_observation_ids == ("edge_absence",)
    assert result.next_observations.candidate_ids == ("fitness_response",)
    assert result.next_observations.ranked is False
