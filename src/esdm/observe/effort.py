"""Observation-effort fields, separate from ecological intensity."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math


@dataclass(frozen=True, slots=True)
class EffortField:
    values: Mapping[tuple[str, int, int], float]

    def __post_init__(self) -> None:
        cleaned: dict[tuple[str, int, int], float] = {}
        for key, value in self.values.items():
            if not isinstance(key, tuple) or len(key) != 3:
                raise ValueError("effort keys must be (space, doy, hour)")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError("effort values must be finite and non-negative")
            cleaned[(str(key[0]), int(key[1]), int(key[2]))] = numeric
        object.__setattr__(self, "values", MappingProxyType(cleaned))

    def at(self, key: tuple[str, int, int]) -> float:
        return float(self.values.get(key, 0.0))
