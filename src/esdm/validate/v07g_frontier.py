"""Deterministic calibration-placement frontier for v0.7g."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math

from esdm.identify.design_rank import design_jacobian_diagnostic
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_CALIBRATION_COUNT,
    V07G_DYNAMIC_TARGETS,
    build_v07g_fixture,
)


_RTOL = 1e-8
_ATOL = 1e-10
_RELATIVE_MIN_THRESHOLD = 1e-3
_CONDITION_THRESHOLD = 1e3
_FISHER_RIDGE = 1e-10


@dataclass(frozen=True, slots=True)
class V07GPlacement:
    placement: tuple[int, ...]
    structural_pass: bool
    conditioning_pass: bool
    target_sd_proxies: dict
    worst_dynamic_sd: float
    condition_number: float
    relative_min_singular_value: float
    total_direct_effort: float


@dataclass(frozen=True, slots=True)
class V07GFrontier:
    rows: tuple[V07GPlacement, ...]
    selected: V07GPlacement
    baseline: V07GPlacement
    selected_to_baseline_worst_sd_ratio: float


def _evaluate_placement(placement) -> V07GPlacement:
    fixture = build_v07g_fixture(placement)

    # One exact JAX Jacobian is sufficient for the whole free-parameter system.
    # Target-specific diagnostics would recompute the identical full Jacobian.
    diagnostic = design_jacobian_diagnostic(
        fixture.training_model,
        fixture.covariates,
        theta=fixture.generating_theta,
        theta_obs=fixture.generating_theta_obs,
        target=next(iter(V07B_TRUTH)),
        rtol=_RTOL,
        atol=_ATOL,
    )

    parameter_count = len(diagnostic.site_names)
    structural_pass = diagnostic.full_rank == parameter_count
    singular = diagnostic.singular_values
    if not singular or not structural_pass:
        relative_min = 0.0
        condition = math.inf
    else:
        largest = float(singular[0])
        smallest = float(singular[-1])
        relative_min = 0.0 if largest <= 0.0 else smallest / largest
        condition = math.inf if smallest <= 0.0 else largest / smallest

    conditioning_pass = (
        structural_pass
        and relative_min >= _RELATIVE_MIN_THRESHOLD
        and condition <= _CONDITION_THRESHOLD
    )

    import jax.numpy as jnp

    jacobian = jnp.asarray(diagnostic.jacobian)
    expected = jnp.asarray(diagnostic.expected_rates)
    fisher = jacobian.T @ (expected[:, None] * jacobian)
    diagonal = jnp.diag(fisher)
    scale = max(1.0, float(jnp.max(diagonal))) if int(diagonal.shape[0]) else 1.0
    regularized = (
        fisher
        + _FISHER_RIDGE * scale * jnp.eye(parameter_count)
    )
    covariance = jnp.linalg.inv(regularized)

    sd = {}
    for target in V07B_TRUTH:
        if target not in diagnostic.site_names:
            raise KeyError(f"v0.7g target missing from Jacobian: {target}")
        index = diagnostic.site_names.index(target)
        variance = max(0.0, float(covariance[index, index]))
        sd[target] = math.sqrt(variance)

    worst_dynamic = max(sd[target] for target in V07G_DYNAMIC_TARGETS)
    return V07GPlacement(
        placement=tuple(int(value) for value in placement),
        structural_pass=structural_pass,
        conditioning_pass=conditioning_pass,
        target_sd_proxies=sd,
        worst_dynamic_sd=float(worst_dynamic),
        condition_number=float(condition),
        relative_min_singular_value=float(relative_min),
        total_direct_effort=float(fixture.total_direct_effort),
    )


def evaluate_v07g_frontier() -> V07GFrontier:
    rows = tuple(
        _evaluate_placement(placement)
        for placement in combinations(range(1, 9), V07G_CALIBRATION_COUNT)
    )
    if len(rows) != 70:
        raise RuntimeError("v0.7g frontier must contain exactly 70 placements")

    eligible = tuple(
        row
        for row in rows
        if row.structural_pass and row.conditioning_pass
    )
    if not eligible:
        raise RuntimeError("v0.7g frontier has no eligible placement")

    selected = min(
        eligible,
        key=lambda row: (row.worst_dynamic_sd, row.placement),
    )
    baseline = next(
        row
        for row in rows
        if row.placement == V07G_BASELINE_PLACEMENT
    )
    return V07GFrontier(
        rows=rows,
        selected=selected,
        baseline=baseline,
        selected_to_baseline_worst_sd_ratio=(
            selected.worst_dynamic_sd / baseline.worst_dynamic_sd
        ),
    )
