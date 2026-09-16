"""Generic ecological state-axis definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateAxis:
    """A named, ordered set of ecological states.

    The axis is deliberately domain-agnostic. Examples may use activity,
    phenology, vertical layer, resource use, or binary occurrence states.
    """

    name: str
    states: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("state-axis name must be a non-empty string")
        if len(self.states) < 2:
            raise ValueError("state axis must declare at least two states")
        if any(not isinstance(state, str) or not state.strip() for state in self.states):
            raise ValueError("state labels must be non-empty strings")
        if len(set(self.states)) != len(self.states):
            raise ValueError("state labels must be unique")
