"""Ordered array containers for backend-efficient model evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


ContextKey = tuple[str, int, int]


@dataclass(frozen=True, slots=True)
class ContextArray:
    """One array whose leading axis follows an explicit context-key order."""

    keys: tuple[ContextKey, ...]
    values: object

    def __post_init__(self) -> None:
        cleaned: list[ContextKey] = []
        for key in self.keys:
            if not isinstance(key, tuple) or len(key) != 3:
                raise ValueError("context-array keys must be (space, doy, hour)")
            cleaned.append((str(key[0]), int(key[1]), int(key[2])))
        keys = tuple(cleaned)
        if len(set(keys)) != len(keys):
            raise ValueError("context-array keys must be unique")
        shape = getattr(self.values, "shape", None)
        if shape is not None:
            if len(shape) < 1:
                raise ValueError("context-array values require a leading context axis")
            if int(shape[0]) != len(keys):
                raise ValueError("context-array leading axis must match key count")
        object.__setattr__(self, "keys", keys)


@dataclass(frozen=True, slots=True)
class LatentFieldArrays:
    """Array-first latent fields keyed by species, with contexts on axis zero."""

    log_intensity: Mapping[str, ContextArray]

    def __post_init__(self) -> None:
        cleaned: dict[str, ContextArray] = {}
        for species, values in self.log_intensity.items():
            name = str(species).strip()
            if not name:
                raise ValueError("latent-field species names must be non-empty")
            if not isinstance(values, ContextArray):
                raise TypeError("latent-field arrays must contain ContextArray values")
            cleaned[name] = values
        object.__setattr__(self, "log_intensity", MappingProxyType(cleaned))
