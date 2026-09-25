"""Deterministic expected-record matched information control for v0.7h."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.identify.design_rank import design_jacobian_diagnostic
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import V07G_DYNAMIC_TARGETS
from .v07h_fixture import (
    V07H_BASELINE_TOTAL_EFFORT,
    V07H_SELECTED_TOTAL_EFFORT,
    build_v07h_fixture,
    expected_direct_count,
)


_RTOL = 1e-8
_ATOL = 1e-10
_RIDGE = 1e-10


@dataclass(frozen=True, slots=True)
class V07HDesignDiagnostic:
    label: str
    target_sd_proxies: dict
    worst_dynamic_sd: float
    condition_number: float
    relative_min_singular_value: float
    expected_direct_count: float
    total_direct_effort: float


@dataclass(frozen=True, slots=True)
class V07HComparison:
    selected: V07HDesignDiagnostic
    baseline: V07HDesignDiagnostic
    selected_to_baseline_worst_sd_ratio: float
    expected_count_relative_error: float
    selected_to_baseline_effort_ratio: float


def _diagnose(label, model, fixture, total_effort):
    diagnostic = design_jacobian_diagnostic(
        model,
        fixture.covariates,
        theta=fixture.generating_theta,
        theta_obs=fixture.generating_theta_obs,
        target=next(iter(V07B_TRUTH)),
        rtol=_RTOL,
        atol=_ATOL,
    )
    parameter_count = len(diagnostic.site_names)
    if diagnostic.full_rank != parameter_count:
        raise RuntimeError(f"v0.7h {label} design is not full-rank")

    largest = float(diagnostic.singular_values[0])
    smallest = float(diagnostic.singular_values[-1])
    condition = largest / smallest
    relative_min = smallest / largest

    import jax.numpy as jnp

    jacobian = jnp.asarray(diagnostic.jacobian)
    expected = jnp.asarray(diagnostic.expected_rates)
    fisher = jacobian.T @ (expected[:, None] * jacobian)
    diagonal = jnp.diag(fisher)
    scale = max(1.0, float(jnp.max(diagonal)))
    covariance = jnp.linalg.inv(
        fisher + _RIDGE * scale * jnp.eye(parameter_count)
    )
    sd = {}
    for target in V07B_TRUTH:
        index = diagnostic.site_names.index(target)
        variance = max(0.0, float(covariance[index, index]))
        sd[target] = math.sqrt(variance)

    return V07HDesignDiagnostic(
        label=str(label),
        target_sd_proxies=sd,
        worst_dynamic_sd=max(sd[target] for target in V07G_DYNAMIC_TARGETS),
        condition_number=condition,
        relative_min_singular_value=relative_min,
        expected_direct_count=expected_direct_count(model, fixture),
        total_direct_effort=float(total_effort),
    )


def evaluate_v07h_comparison() -> V07HComparison:
    fixture = build_v07h_fixture()
    selected = _diagnose(
        "selected",
        fixture.selected_model,
        fixture,
        V07H_SELECTED_TOTAL_EFFORT,
    )
    baseline = _diagnose(
        "baseline",
        fixture.baseline_model,
        fixture,
        V07H_BASELINE_TOTAL_EFFORT,
    )
    relative_error = abs(
        selected.expected_direct_count - baseline.expected_direct_count
    ) / baseline.expected_direct_count

    return V07HComparison(
        selected=selected,
        baseline=baseline,
        selected_to_baseline_worst_sd_ratio=(
            selected.worst_dynamic_sd / baseline.worst_dynamic_sd
        ),
        expected_count_relative_error=relative_error,
        selected_to_baseline_effort_ratio=(
            selected.total_direct_effort / baseline.total_direct_effort
        ),
    )
