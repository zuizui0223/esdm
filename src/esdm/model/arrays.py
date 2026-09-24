"""Ordered array containers for backend-efficient model evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


ContextKey = tuple[str, int, int]


def _clean_keys(raw_keys) -> tuple[ContextKey, ...]:
    cleaned: list[ContextKey] = []
    for key in raw_keys:
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("context-array keys must be (space, doy, hour)")
        cleaned.append((str(key[0]), int(key[1]), int(key[2])))
    keys = tuple(cleaned)
    if len(set(keys)) != len(keys):
        raise ValueError("context-array keys must be unique")
    return keys


@dataclass(frozen=True, slots=True)
class ContextArray:
    """One array whose leading axis follows an explicit context-key order."""

    keys: tuple[ContextKey, ...]
    values: object

    def __post_init__(self) -> None:
        keys = _clean_keys(self.keys)
        shape = getattr(self.values, "shape", None)
        if shape is not None:
            if len(shape) < 1:
                raise ValueError("context-array values require a leading context axis")
            if int(shape[0]) != len(keys):
                raise ValueError("context-array leading axis must match key count")
        object.__setattr__(self, "keys", keys)


@dataclass(frozen=True, slots=True)
class ContextStateArray:
    """A context x state array with explicit ordered labels on both axes."""

    keys: tuple[ContextKey, ...]
    states: tuple[str, ...]
    values: object

    def __post_init__(self) -> None:
        keys = _clean_keys(self.keys)
        states = tuple(str(state).strip() for state in self.states)
        if (
            not states
            or any(not state for state in states)
            or len(set(states)) != len(states)
        ):
            raise ValueError("state labels must be unique non-empty strings")
        shape = getattr(self.values, "shape", None)
        if shape is not None:
            if len(shape) != 2:
                raise ValueError("state-array values must be two-dimensional")
            if int(shape[0]) != len(keys) or int(shape[1]) != len(states):
                raise ValueError("state-array shape must be context x state")
        object.__setattr__(self, "keys", keys)
        object.__setattr__(self, "states", states)


def _freeze_context_mapping(values, *, label: str):
    cleaned: dict[str, ContextArray] = {}
    for species, array in values.items():
        name = str(species).strip()
        if not name:
            raise ValueError(f"{label} species names must be non-empty")
        if not isinstance(array, ContextArray):
            raise TypeError(f"{label} must contain ContextArray values")
        cleaned[name] = array
    return MappingProxyType(cleaned)


def _freeze_state_mapping(values, *, label: str):
    cleaned: dict[str, ContextStateArray] = {}
    for species, array in values.items():
        name = str(species).strip()
        if not name:
            raise ValueError(f"{label} species names must be non-empty")
        if not isinstance(array, ContextStateArray):
            raise TypeError(f"{label} must contain ContextStateArray values")
        cleaned[name] = array
    return MappingProxyType(cleaned)


@dataclass(frozen=True, slots=True)
class LatentFieldArrays:
    """Array-first latent ecological fields with contexts on axis zero."""

    log_intensity: Mapping[str, ContextArray]
    log_accessibility: Mapping[str, ContextArray] = field(default_factory=dict)
    accessibility: Mapping[str, ContextArray] = field(default_factory=dict)
    activity_logit: Mapping[str, ContextArray] = field(default_factory=dict)
    activity: Mapping[str, ContextArray] = field(default_factory=dict)
    state_logits: Mapping[str, ContextStateArray] = field(default_factory=dict)
    state_probabilities: Mapping[str, ContextStateArray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        log_intensity = _freeze_context_mapping(
            self.log_intensity, label="log-intensity arrays"
        )
        log_accessibility = _freeze_context_mapping(
            self.log_accessibility, label="log-accessibility arrays"
        )
        accessibility = _freeze_context_mapping(
            self.accessibility, label="accessibility arrays"
        )
        activity_logit = _freeze_context_mapping(
            self.activity_logit, label="activity-logit arrays"
        )
        activity = _freeze_context_mapping(
            self.activity, label="activity arrays"
        )
        state_logits = _freeze_state_mapping(
            self.state_logits, label="state-logit arrays"
        )
        state_probabilities = _freeze_state_mapping(
            self.state_probabilities, label="state-probability arrays"
        )

        known = set(log_intensity)
        for label, mapping in (
            ("log-accessibility", log_accessibility),
            ("accessibility", accessibility),
            ("activity-logit", activity_logit),
            ("activity", activity),
            ("state-logit", state_logits),
            ("state-probability", state_probabilities),
        ):
            unknown = set(mapping) - known
            if unknown:
                raise ValueError(
                    f"{label} arrays contain species without log intensity: {sorted(unknown)}"
                )

        for species, base in log_intensity.items():
            for mapping in (
                log_accessibility,
                accessibility,
                activity_logit,
                activity,
            ):
                if species in mapping and mapping[species].keys != base.keys:
                    raise ValueError("latent channel context orders must match")
            if species in state_logits and state_logits[species].keys != base.keys:
                raise ValueError("latent channel context orders must match")
            if (
                species in state_probabilities
                and state_probabilities[species].keys != base.keys
            ):
                raise ValueError("latent channel context orders must match")
            if species in state_logits and species in state_probabilities:
                if state_logits[species].states != state_probabilities[species].states:
                    raise ValueError("state logit/probability labels must match")

        object.__setattr__(self, "log_intensity", log_intensity)
        object.__setattr__(self, "log_accessibility", log_accessibility)
        object.__setattr__(self, "accessibility", accessibility)
        object.__setattr__(self, "activity_logit", activity_logit)
        object.__setattr__(self, "activity", activity)
        object.__setattr__(self, "state_logits", state_logits)
        object.__setattr__(self, "state_probabilities", state_probabilities)
