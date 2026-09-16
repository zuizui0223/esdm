"""Finite declared ecological-world compatibility and contraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from collections.abc import Iterable, Mapping

from esdm.authorization import AuthorizedObservation


WORLD_EVIDENCE_STATES = {"positive", "negative"}


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be a non-empty string")
    return result


def _normalize_expected(value: object) -> frozenset[str]:
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(value)  # type: ignore[arg-type]
        except TypeError as exc:
            raise ValueError("world prediction must be a state or iterable of states") from exc
    normalized = frozenset(_text(item, "world evidence state") for item in values)
    if not normalized:
        raise ValueError("world prediction state set must be non-empty")
    unknown = normalized - WORLD_EVIDENCE_STATES
    if unknown:
        raise ValueError(f"unknown world evidence state(s): {sorted(unknown)}")
    return normalized


@dataclass(frozen=True, slots=True)
class EcologicalWorld:
    world_id: str
    predictions: Mapping[str, object]

    def __post_init__(self) -> None:
        world_id = _text(self.world_id, "world_id")
        normalized: dict[str, frozenset[str]] = {}
        for observation_id, expected in dict(self.predictions).items():
            key = _text(observation_id, "observation_id")
            if key in normalized:
                raise ValueError("duplicate world observation prediction")
            normalized[key] = _normalize_expected(expected)
        object.__setattr__(self, "world_id", world_id)
        object.__setattr__(self, "predictions", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class EcologicalWorldSet:
    worlds: tuple[EcologicalWorld, ...]
    surviving_world_ids: tuple[str, ...] | None = field(default=None)

    def __post_init__(self) -> None:
        worlds = tuple(self.worlds)
        if not worlds:
            raise ValueError("at least one declared ecological world is required")
        ids = tuple(world.world_id for world in worlds)
        if len(set(ids)) != len(ids):
            raise ValueError("ecological world IDs must be unique")

        if self.surviving_world_ids is None:
            surviving = ids
        else:
            requested = tuple(_text(value, "surviving_world_id") for value in self.surviving_world_ids)
            if len(set(requested)) != len(requested):
                raise ValueError("surviving world IDs must be unique")
            unknown = set(requested) - set(ids)
            if unknown:
                raise ValueError(f"surviving worlds outside declared universe: {sorted(unknown)}")
            requested_set = set(requested)
            surviving = tuple(world_id for world_id in ids if world_id in requested_set)

        object.__setattr__(self, "worlds", worlds)
        object.__setattr__(self, "surviving_world_ids", surviving)

    @property
    def declared_world_ids(self) -> tuple[str, ...]:
        return tuple(world.world_id for world in self.worlds)

    @property
    def identifiable_within_declared_universe(self) -> bool:
        return len(self.surviving_world_ids) == 1

    def world_by_id(self, world_id: str) -> EcologicalWorld:
        for world in self.worlds:
            if world.world_id == world_id:
                return world
        raise KeyError(world_id)


@dataclass(frozen=True, slots=True)
class WorldContraction:
    before: EcologicalWorldSet
    after: EcologicalWorldSet
    eliminated_world_ids: tuple[str, ...]
    ignored_observation_ids: tuple[str, ...]
    used_observation_ids: tuple[str, ...]

    @property
    def contracted(self) -> bool:
        return len(self.after.surviving_world_ids) < len(self.before.surviving_world_ids)


def contract_world_set(
    world_set: EcologicalWorldSet,
    observations: Iterable[AuthorizedObservation],
) -> WorldContraction:
    """Contract a declared world set using authorized evidence only.

    ``unavailable`` observations are ignored. A world is eliminated only when it made
    an explicit prediction for the observation and that prediction is incompatible
    with the authorized positive/negative state. Worlds that make no declaration for
    the observation are retained rather than guessed against.
    """

    survivors = list(world_set.surviving_world_ids)
    ignored: list[str] = []
    used: list[str] = []

    for observation in tuple(observations):
        if observation.evidence_state == "unavailable":
            ignored.append(observation.observation_id)
            continue
        if observation.evidence_state not in WORLD_EVIDENCE_STATES:
            raise ValueError("world contraction accepts only authorized positive/negative/unavailable states")
        used.append(observation.observation_id)
        next_survivors: list[str] = []
        for world_id in survivors:
            world = world_set.world_by_id(world_id)
            expected = world.predictions.get(observation.observation_id)
            if expected is None or observation.evidence_state in expected:
                next_survivors.append(world_id)
        survivors = next_survivors

    after = EcologicalWorldSet(world_set.worlds, tuple(survivors))
    survivor_set = set(after.surviving_world_ids)
    eliminated = tuple(
        world_id
        for world_id in world_set.surviving_world_ids
        if world_id not in survivor_set
    )
    return WorldContraction(
        before=world_set,
        after=after,
        eliminated_world_ids=eliminated,
        ignored_observation_ids=tuple(ignored),
        used_observation_ids=tuple(used),
    )
