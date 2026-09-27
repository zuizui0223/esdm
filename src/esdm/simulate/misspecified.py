"""Deliberately misspecified benchmark worlds.

These diagnostics are not SBC worlds. They ask how a fitted simplification can be biased
when the data-generating observation process lies outside the assumed model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def _clean_vector(values: Sequence[float], label: str) -> tuple[float, ...]:
    cleaned = tuple(float(value) for value in values)
    if not cleaned or any(not math.isfinite(value) for value in cleaned):
        raise ValueError(f"{label} must be non-empty and finite")
    return cleaned


def _projection_slope(x: Sequence[float], y: Sequence[float]) -> float:
    xx = _clean_vector(x, "covariate")
    yy = _clean_vector(y, "response")
    if len(xx) != len(yy):
        raise ValueError("projection vectors must have equal length")
    mean_x = sum(xx) / len(xx)
    mean_y = sum(yy) / len(yy)
    denominator = sum((value - mean_x) ** 2 for value in xx)
    if denominator <= 0.0:
        raise ValueError("covariate must have positive variance")
    numerator = sum((xv - mean_x) * (yv - mean_y) for xv, yv in zip(xx, yy))
    return numerator / denominator


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


def effort_gradient_apparent_slope(
    *,
    true_beta: float,
    covariate: Sequence[float],
    true_effort: Sequence[float],
    assumed_effort: float,
) -> float:
    """Expected slope after projecting an unmodelled effort gradient onto a covariate.

    If the true record intensity is

    `exp(alpha + beta*x) * effort_true(x)`

    but the fitted model replaces effort by a constant, the apparent ecological slope
    gains the least-squares projection of `log(effort_true / effort_assumed)` onto `x`.
    This is a deterministic misspecification diagnostic, not an estimator.
    """

    x = _clean_vector(covariate, "covariate")
    effort = _clean_vector(true_effort, "true_effort")
    if len(x) != len(effort):
        raise ValueError("covariate and true_effort must have equal length")
    assumed = float(assumed_effort)
    if not math.isfinite(assumed) or assumed <= 0.0:
        raise ValueError("assumed_effort must be finite and positive")
    if any(value <= 0.0 for value in effort):
        raise ValueError("true_effort must be strictly positive for slope projection")
    residual_log_effort = tuple(math.log(value / assumed) for value in effort)
    return float(true_beta) + _projection_slope(x, residual_log_effort)


def omitted_driver_apparent_slope(
    *,
    true_beta: float,
    omitted_beta: float,
    covariate: Sequence[float],
    hidden_driver: Sequence[float],
) -> float:
    """Expected slope under linear omitted-variable projection.

    For a generating linear predictor `beta*x + gamma*h`, fitting only `x` gives the
    population projection `beta + gamma * Cov(x, h) / Var(x)` under equal weighting.
    This diagnostic makes the direction and magnitude of hidden-driver bias explicit.
    """

    x = _clean_vector(covariate, "covariate")
    hidden = _clean_vector(hidden_driver, "hidden_driver")
    if len(x) != len(hidden):
        raise ValueError("covariate and hidden_driver must have equal length")
    return float(true_beta) + float(omitted_beta) * _projection_slope(x, hidden)
