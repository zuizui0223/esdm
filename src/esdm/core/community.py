"""Community-level taxon and ecological-state probability objects."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


_TOLERANCE = 1e-9


def _validate_probability_mapping(values: Mapping[str, float], *, label: str) -> dict[str, float]:
    if not values:
        raise ValueError(f"{label} must not be empty")
    normalized: dict[str, float] = {}
    for key, raw in values.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{label} keys must be non-empty strings")
        value = float(raw)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{label} probabilities must be finite and non-negative")
        normalized[key] = value
    total = sum(normalized.values())
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=_TOLERANCE):
        raise ValueError(f"{label} probabilities must sum to one")
    return normalized


@dataclass(frozen=True, slots=True)
class CommunityStateDistribution:
    """Joint taxon/state distribution represented as P(taxon) P(state | taxon)."""

    taxon_weights: Mapping[str, float]
    state_probabilities: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        taxon_weights = _validate_probability_mapping(self.taxon_weights, label="taxon weights")
        if set(taxon_weights) != set(self.state_probabilities):
            raise ValueError("taxon sets must match between weights and state probabilities")

        state_probabilities: dict[str, dict[str, float]] = {}
        for taxon in taxon_weights:
            state_probabilities[taxon] = _validate_probability_mapping(
                self.state_probabilities[taxon],
                label=f"state probabilities for taxon {taxon!r}",
            )

        object.__setattr__(self, "taxon_weights", taxon_weights)
        object.__setattr__(self, "state_probabilities", state_probabilities)

    @property
    def taxa(self) -> tuple[str, ...]:
        return tuple(self.taxon_weights)

    def joint_probabilities(self) -> dict[tuple[str, str], float]:
        joint: dict[tuple[str, str], float] = {}
        for taxon, weight in self.taxon_weights.items():
            for state, conditional_probability in self.state_probabilities[taxon].items():
                joint[(taxon, state)] = weight * conditional_probability
        return joint
