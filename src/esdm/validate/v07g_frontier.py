"""Deterministic calibration-placement frontier for v0.7g."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_CALIBRATION_COUNT,
    V07G_DYNAMIC_TARGETS,
    build_v07g_fixture,
)


_STRUCTURAL = {
    "method": "jax",
    "rtol": 1e-8,
    "atol": 1e-10,
}

_PRACTICAL = {
    "rtol": 1e-8,
    "atol": 1e-10,
    "relative_singular_value_threshold": 1e-3,
    "condition_number_threshold": 1e3,
    "target_sd_threshold": None,
    "fisher_ridge": 1e-10,
}


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
    evidence = {}
    for target in V07B_TRUTH:
        evidence[target] = diagnose_identification(
            fixture.training_model,
            fixture.covariates,
            theta=fixture.generating_theta,
            theta_obs=fixture.generating_theta_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    structural_pass = all(
        row.structural.status is IdentificationStatus.IDENTIFIED
        for row in evidence.values()
    )
    practical_rows = [row.practical for row in evidence.values()]
    if any(row is None for row in practical_rows):
        raise RuntimeError("v0.7g practical diagnostics unexpectedly absent")

    condition_number = max(float(row.condition_number) for row in practical_rows)
    relative_min = min(
        float(row.relative_min_singular_value)
        for row in practical_rows
    )
    conditioning_pass = (
        structural_pass
        and condition_number <= _PRACTICAL["condition_number_threshold"]
        and relative_min >= _PRACTICAL["relative_singular_value_threshold"]
    )
    sd = {
        target: float(evidence[target].practical.target_sd_proxy)
        for target in V07B_TRUTH
    }
    worst_dynamic = max(sd[target] for target in V07G_DYNAMIC_TARGETS)
    return V07GPlacement(
        placement=tuple(int(value) for value in placement),
        structural_pass=structural_pass,
        conditioning_pass=conditioning_pass,
        target_sd_proxies=sd,
        worst_dynamic_sd=float(worst_dynamic),
        condition_number=float(condition_number),
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
