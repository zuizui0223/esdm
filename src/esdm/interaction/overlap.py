"""Overlap metrics for geography and ecological state space."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def _normalize(values: Iterable[float]) -> list[float]:
    normalized = [float(value) for value in values]
    if not normalized:
        raise ValueError("overlap vector must not be empty")
    if any(not math.isfinite(value) or value < 0.0 for value in normalized):
        raise ValueError("overlap values must be finite and non-negative")
    total = sum(normalized)
    if total <= 0.0:
        raise ValueError("overlap vector must have positive total mass")
    return [value / total for value in normalized]


def overlap_coefficient(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = _normalize(left)
    right_values = _normalize(right)
    if len(left_values) != len(right_values):
        raise ValueError("overlap vectors must have equal length")
    return sum(min(a, b) for a, b in zip(left_values, right_values, strict=True))


def geographic_overlap(left: Iterable[float], right: Iterable[float]) -> float:
    """Normalized overlap between two spatial-use distributions."""

    return overlap_coefficient(left, right)


def state_overlap(
    left: Mapping[str, float],
    right: Mapping[str, float],
) -> float:
    """Normalized overlap between two ecological-state distributions."""

    states = sorted(set(left) | set(right))
    if not states:
        raise ValueError("state distributions must not be empty")
    return overlap_coefficient(
        [left.get(state, 0.0) for state in states],
        [right.get(state, 0.0) for state in states],
    )
