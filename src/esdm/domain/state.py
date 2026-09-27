"""Ecological state declarations and refinement chains."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class StateSpace:
    states: tuple[str, ...]

    def __post_init__(self) -> None:
        states = tuple(str(value).strip() for value in self.states)
        if not states or any(not value for value in states) or len(set(states)) != len(states):
            raise ValueError("states must contain unique non-empty labels")
        object.__setattr__(self, "states", states)


@dataclass(frozen=True, slots=True)
class Partition:
    name: str
    groups: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("partition name must be non-empty")
        groups = {
            str(label).strip(): tuple(str(value).strip() for value in members)
            for label, members in self.groups.items()
        }
        if not groups or any(not label for label in groups):
            raise ValueError("partition groups require non-empty labels")
        flattened = [state for members in groups.values() for state in members]
        if any(not state for state in flattened) or len(set(flattened)) != len(flattened):
            raise ValueError("partition groups must contain each state at most once")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "groups", MappingProxyType(groups))

    def group_for(self, state: str) -> str:
        for label, members in self.groups.items():
            if state in members:
                return label
        raise KeyError(state)


@dataclass(frozen=True, slots=True)
class RefinementChain:
    state_space: StateSpace
    partitions: tuple[Partition, ...]

    def __post_init__(self) -> None:
        partitions = tuple(self.partitions)
        if not partitions:
            raise ValueError("at least one partition is required")
        expected = set(self.state_space.states)
        for partition in partitions:
            covered = {state for members in partition.groups.values() for state in members}
            if covered != expected:
                raise ValueError("every partition must cover the full state space exactly")
        for coarse, fine in zip(partitions, partitions[1:]):
            for members in fine.groups.values():
                coarse_labels = {coarse.group_for(state) for state in members}
                if len(coarse_labels) != 1:
                    raise ValueError("later partitions must refine earlier partitions")
        object.__setattr__(self, "partitions", partitions)

    @property
    def finest(self) -> Partition:
        return self.partitions[-1]
