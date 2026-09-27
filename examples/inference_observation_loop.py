"""Generic Phase-3 inference/observation cycle example."""

from esdm.authorization import ObservationRecord
from esdm.inference import run_inference_observation_cycle
from esdm.observe import ObservationCandidate
from esdm.process import ProcessSupportSet, SeparatorEvidence
from esdm.worlds import EcologicalWorld, EcologicalWorldSet


result = run_inference_observation_cycle(
    raw_observations=(
        ObservationRecord("edge_presence", "positive"),
        ObservationRecord("edge_absence", "negative", negative_gate_passed=False),
    ),
    process_support=ProcessSupportSet(
        ("shared_environment", "competition", "mutualism")
    ),
    separator_evidence=(
        SeparatorEvidence(
            "shared_environment",
            "independent_measurement",
            "exclude",
            True,
            True,
            True,
        ),
        SeparatorEvidence(
            "competition",
            "independent_measurement",
            "compatible",
            True,
            True,
            True,
        ),
        SeparatorEvidence(
            "mutualism",
            "independent_measurement",
            "compatible",
            True,
            True,
            True,
        ),
    ),
    required_separator_ids=("independent_measurement",),
    world_set=EcologicalWorldSet(
        (
            EcologicalWorld("shared_environment", {"edge_presence": "negative"}),
            EcologicalWorld("competition", {"edge_presence": "positive"}),
            EcologicalWorld("mutualism", {"edge_presence": "positive"}),
        )
    ),
    observation_candidates=(
        ObservationCandidate(
            "fitness_response",
            {"competition": "negative", "mutualism": "positive"},
        ),
    ),
)

assert result.process_refinement.refined.members == ("competition", "mutualism")
assert result.world_contraction.after.surviving_world_ids == (
    "competition",
    "mutualism",
)
assert result.next_observations.candidate_ids == ("fitness_response",)
assert result.next_observations.ranked is False
