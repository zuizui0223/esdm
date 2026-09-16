"""Generic state-compatibility opportunity for biotic edges."""

from __future__ import annotations

import math
from collections.abc import Mapping


def _validate_distribution(values: Mapping[str, float], *, label: str) -> dict[str, float]:
    if not values:
        raise ValueError(f"{label} must not be empty")
    checked: dict[str, float] = {}
    for state, raw in values.items():
        if not isinstance(state, str) or not state.strip():
            raise ValueError(f"{label} state labels must be non-empty strings")
        value = float(raw)
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{label} probabilities must be finite and non-negative")
        checked[state] = value
    if not math.isclose(sum(checked.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{label} probabilities must sum to one")
    return checked


def interaction_opportunity(
    source_states: Mapping[str, float],
    target_states: Mapping[str, float],
    compatibility: Mapping[tuple[str, str], float],
) -> float:
    """Return expected state compatibility in [0, 1].

    This is a potential edge opportunity under the supplied state distributions
    and compatibility kernel. It is not a realized-interaction probability.
    """

    source = _validate_distribution(source_states, label="source state distribution")
    target = _validate_distribution(target_states, label="target state distribution")

    expected = 0.0
    for source_state, source_probability in source.items():
        for target_state, target_probability in target.items():
            raw = compatibility.get((source_state, target_state), 0.0)
            value = float(raw)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("compatibility values must be finite and within [0, 1]")
            expected += source_probability * target_probability * value
    return expected
