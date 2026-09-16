"""Non-ranked next-observation candidate sets for unresolved ecological worlds."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Iterable, Mapping

from esdm.worlds import EcologicalWorldSet


OUTCOMES = {"positive", "negative"}


def _text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


@dataclass(frozen=True, slots=True)
class ObservationCandidate:
    candidate_id: str
    outcomes_by_world: Mapping[str, str]

    def __post_init__(self) -> None:
        candidate_id = _text(self.candidate_id, "candidate_id")
        outcomes: dict[str, str] = {}
        for world_id, outcome in dict(self.outcomes_by_world).items():
            wid = _text(world_id, "world_id")
            state = _text(outcome, "outcome")
            if state not in OUTCOMES:
                raise ValueError(f"unknown candidate outcome: {state}")
            outcomes[wid] = state
        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(self, "outcomes_by_world", MappingProxyType(outcomes))


@dataclass(frozen=True, slots=True)
class DiscriminatingObservationSet:
    candidate_ids: tuple[str, ...]
    ranked: bool = False
    claim: str = "discriminating_candidate_set"


def nominate_discriminating_observations(
    world_set: EcologicalWorldSet,
    candidates: Iterable[ObservationCandidate],
) -> DiscriminatingObservationSet:
    """Return all candidates that split the current surviving declared worlds.

    The output order is deterministic lexical order only. It is not a scientific
    ranking, occupancy score, expected-information-gain optimum, route, or effort plan.
    """

    declared_worlds = set(world_set.declared_world_ids)
    survivors = set(world_set.surviving_world_ids)
    seen_ids: set[str] = set()
    admitted: list[str] = []

    for candidate in tuple(candidates):
        if candidate.candidate_id in seen_ids:
            raise ValueError("candidate IDs must be unique")
        seen_ids.add(candidate.candidate_id)
        unknown_worlds = set(candidate.outcomes_by_world) - declared_worlds
        if unknown_worlds:
            raise ValueError(f"candidate predictions outside declared world universe: {sorted(unknown_worlds)}")
        states = {
            outcome
            for world_id, outcome in candidate.outcomes_by_world.items()
            if world_id in survivors
        }
        if len(states) >= 2:
            admitted.append(candidate.candidate_id)

    return DiscriminatingObservationSet(candidate_ids=tuple(sorted(admitted)))
