"""Held-out predictive gain from adding biotic information."""

from __future__ import annotations

import math
from collections.abc import Iterable


def _finite_vector(values: Iterable[float], *, label: str) -> list[float]:
    vector = [float(value) for value in values]
    if not vector:
        raise ValueError(f"{label} must not be empty")
    if any(not math.isfinite(value) for value in vector):
        raise ValueError(f"{label} must contain only finite values")
    return vector


def biotic_information_gain(
    log_score_without_biotic: Iterable[float],
    log_score_with_biotic: Iterable[float],
    *,
    weights: Iterable[float] | None = None,
) -> float:
    """Return weighted held-out mean score gain from adding biotic information.

    Positive values indicate predictive improvement under the supplied held-out
    scores. The result is predictive dependence, not causal interaction evidence.
    """

    baseline = _finite_vector(log_score_without_biotic, label="baseline log scores")
    augmented = _finite_vector(log_score_with_biotic, label="biotic log scores")
    if len(baseline) != len(augmented):
        raise ValueError("score vectors must have equal length")

    if weights is None:
        weight_values = [1.0] * len(baseline)
    else:
        weight_values = _finite_vector(weights, label="weights")
        if len(weight_values) != len(baseline):
            raise ValueError("weights must match score-vector length")
        if any(value < 0.0 for value in weight_values):
            raise ValueError("weights must be non-negative")

    total_weight = sum(weight_values)
    if total_weight <= 0.0:
        raise ValueError("weights must have positive total mass")

    return sum(
        weight * (with_biotic - without_biotic)
        for without_biotic, with_biotic, weight in zip(
            baseline,
            augmented,
            weight_values,
            strict=True,
        )
    ) / total_weight
