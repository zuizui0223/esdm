"""Discrete space × day-of-year × hour domain declarations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True, slots=True)
class Context:
    space: str
    doy: int
    hour: int

    @property
    def key(self) -> tuple[str, int, int]:
        return (self.space, self.doy, self.hour)


@dataclass(frozen=True, slots=True)
class Grid:
    space: tuple[str, ...]
    doy: tuple[int, ...]
    hour: tuple[int, ...]

    def __post_init__(self) -> None:
        space = tuple(str(value).strip() for value in self.space)
        if not space or any(not value for value in space) or len(set(space)) != len(space):
            raise ValueError("space must contain unique non-empty IDs")
        doy = tuple(int(value) for value in self.doy)
        if not doy or len(set(doy)) != len(doy) or any(value < 1 or value > 366 for value in doy):
            raise ValueError("doy must contain unique integers in 1..366")
        hour = tuple(int(value) for value in self.hour)
        if not hour or len(set(hour)) != len(hour) or any(value < 0 or value > 23 for value in hour):
            raise ValueError("hour must contain unique integers in 0..23")
        object.__setattr__(self, "space", space)
        object.__setattr__(self, "doy", doy)
        object.__setattr__(self, "hour", hour)

    def contexts(self):
        for space, doy, hour in product(self.space, self.doy, self.hour):
            yield Context(space, doy, hour)

    @property
    def keys(self) -> tuple[tuple[str, int, int], ...]:
        return tuple(context.key for context in self.contexts())
