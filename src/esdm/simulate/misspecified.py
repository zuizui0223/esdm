"""Deliberately misspecified benchmark worlds.

These diagnostics are not SBC worlds. They ask how a fitted simplification can be biased
when the data-generating observation process lies outside the assumed model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def uniform_effort_intercept_bias(
    *,
    true_log_intensity: float,
    true_effort: Sequence[float],
    assumed_effort: float,
) -> float:
    """Expected intercept bias if heterogeneous effort is replaced by one constant.

    With constant ecological intensity, the expected mean record rate is
    `exp(eta_true) * mean(true_effort)`. A naive model dividing by a fixed assumed
    effort therefore shifts the fitted log intensity by
    `log(mean(true_effort) / assumed_effort)`.
    """

    efforts = tuple(float(value) for value in true_effort)
    if not efforts or any(not math.isfinite(value) or value < 0.0 for value in efforts):
        raise ValueError("true_effort must be non-empty, finite, and non-negative")
    assumed = float(assumed_effort)
    if not math.isfinite(assumed) or assumed <= 0.0:
        raise ValueError("assumed_effort must be finite and positive")
    mean_effort = sum(efforts) / len(efforts)
    if mean_effort <= 0.0:
        raise ValueError("mean true effort must be positive")
    _ = float(true_log_intensity)  # retained explicitly as the generating estimand
    return math.log(mean_effort / assumed)
