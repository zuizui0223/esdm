"""End-to-end orchestration for the inference / observation loop.

The process-explanation stream and finite-world stream remain separate. This module
only coordinates their declared inputs; it does not infer process truth from a world
label or vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from esdm.authorization import AuthorizedObservation, ObservationRecord, authorize_observation
from esdm.observe import (
    DiscriminatingObservationSet,
    ObservationCandidate,
    nominate_discriminating_observations,
)
from esdm.process import (
    ProcessRefinement,
    ProcessSupportSet,
    SeparatorEvidence,
    refine_process_support_set,
)
from esdm.worlds import EcologicalWorldSet, WorldContraction, contract_world_set


@dataclass(frozen=True, slots=True)
class InferenceObservationCycle:
    authorized_observations: tuple[AuthorizedObservation, ...]
    process_refinement: ProcessRefinement
    world_contraction: WorldContraction
    next_observations: DiscriminatingObservationSet


def run_inference_observation_cycle(
    *,
    raw_observations: Iterable[ObservationRecord],
    process_support: ProcessSupportSet,
    separator_evidence: Iterable[SeparatorEvidence],
    required_separator_ids: Sequence[str],
    world_set: EcologicalWorldSet,
    observation_candidates: Iterable[ObservationCandidate],
) -> InferenceObservationCycle:
    """Run one declared inference/update cycle.

    Raw observations are authorized first. Process refinement consumes only the
    separately supplied separator-evidence stream. World contraction consumes only
    authorized observations. Candidate nomination is based on the surviving world
    set. No unavailable observation is converted to negative evidence.
    """

    authorized = tuple(authorize_observation(record) for record in raw_observations)
    process_refinement = refine_process_support_set(
        process_support,
        tuple(separator_evidence),
        required_separator_ids=required_separator_ids,
    )
    world_contraction = contract_world_set(world_set, authorized)
    next_observations = nominate_discriminating_observations(
        world_contraction.after,
        tuple(observation_candidates),
    )
    return InferenceObservationCycle(
        authorized_observations=authorized,
        process_refinement=process_refinement,
        world_contraction=world_contraction,
        next_observations=next_observations,
    )
