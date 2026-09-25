"""Burned-pilot plug-in calibration selector for v0.7i."""

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
class V07IPlacementScore:
    placement: tuple[int, ...]
    structural_pass: bool
    conditioning_pass: bool
    worst_dynamic_sd: float
    target_sd_proxies: dict
    condition_number: float
    relative_min_singular_value: float


@dataclass(frozen=True, slots=True)
class V07IPilotSelection:
    selected: V07IPlacementScore
    baseline: V07IPlacementScore
    selected_to_baseline_predicted_ratio: float
    placements_evaluated: int


def theta_from_posterior_means(samples) -> dict:
    """Convert posterior sample sites into the ecological theta mapping.

    The selector receives only posterior draws from the burned pilot fit.
    No generating truth is accepted by this helper.
    """

    site_to_parameter = {
        "sp.suitability.alpha": "alpha",
        "sp.occupancy.psi0_logit": "psi0_logit",
        "sp.occupancy.gamma_logit": "gamma_logit",
        "sp.occupancy.epsilon_logit": "epsilon_logit",
    }
    values = {}
    for site, parameter in site_to_parameter.items():
        if site not in samples:
            raise KeyError(f"pilot samples missing site {site!r}")
        draws = tuple(float(value) for value in samples[site])
        if not draws:
            raise ValueError(f"pilot samples for {site!r} are empty")
        values[parameter] = math.fsum(draws) / len(draws)
    return {"sp": values}


def _score_placement(placement, *, theta) -> V07IPlacementScore:
    fixture = build_v07g_fixture(placement)
    diagnostic = design_jacobian_diagnostic(
        fixture.training_model,
        fixture.covariates,
        theta=theta,
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
    covariance = jnp.linalg.inv(
        fisher + _FISHER_RIDGE * scale * jnp.eye(parameter_count)
    )

    sd = {}
    for target in V07B_TRUTH:
        index = diagnostic.site_names.index(target)
        sd[target] = math.sqrt(
            max(0.0, float(covariance[index, index]))
        )
    return V07IPlacementScore(
        placement=tuple(int(day) for day in placement),
        structural_pass=structural_pass,
        conditioning_pass=conditioning_pass,
        worst_dynamic_sd=max(sd[target] for target in V07G_DYNAMIC_TARGETS),
        target_sd_proxies=sd,
        condition_number=float(condition),
        relative_min_singular_value=float(relative_min),
    )


def select_v07i_placement_from_theta(theta) -> V07IPilotSelection:
    rows = tuple(
        _score_placement(placement, theta=theta)
        for placement in combinations(range(1, 9), V07G_CALIBRATION_COUNT)
    )
    if len(rows) != 70:
        raise RuntimeError("v0.7i selector must evaluate exactly 70 placements")

    eligible = tuple(
        row
        for row in rows
        if row.structural_pass and row.conditioning_pass
    )
    if not eligible:
        raise RuntimeError("burned-pilot selector found no eligible placement")

    selected = min(
        eligible,
        key=lambda row: (row.worst_dynamic_sd, row.placement),
    )
    baseline = next(
        row
        for row in rows
        if row.placement == V07G_BASELINE_PLACEMENT
    )
    return V07IPilotSelection(
        selected=selected,
        baseline=baseline,
        selected_to_baseline_predicted_ratio=(
            selected.worst_dynamic_sd / baseline.worst_dynamic_sd
        ),
        placements_evaluated=len(rows),
    )
