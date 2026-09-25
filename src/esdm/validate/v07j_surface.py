"""Population-shift sensitivity surface for the v0.7i pilot-selected schedule."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import math

from .v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_SELECTED_PLACEMENT,
)
from .v07i_selector import _score_placement


V07J_PSI0_GRID = (0.10, 0.20, 0.50, 0.80)
V07J_GAMMA_GRID = (0.15, 0.35, 0.55)
V07J_EPSILON_GRID = (0.05, 0.15, 0.30)


def _logit(probability: float) -> float:
    p = float(probability)
    return math.log(p / (1.0 - p))


def _theta(psi0: float, gamma: float, epsilon: float):
    return {
        "sp": {
            "alpha": 0.30,
            "psi0_logit": _logit(psi0),
            "gamma_logit": _logit(gamma),
            "epsilon_logit": _logit(epsilon),
        }
    }


@dataclass(frozen=True, slots=True)
class V07JCell:
    psi0: float
    gamma: float
    epsilon: float
    selected_worst_dynamic_sd: float
    baseline_worst_dynamic_sd: float
    selected_to_baseline_ratio: float
    selected_better: bool
    selected_conditioning_pass: bool
    baseline_conditioning_pass: bool
    jointly_eligible: bool
    selected_condition_number: float
    baseline_condition_number: float


@dataclass(frozen=True, slots=True)
class V07JSurface:
    cells: tuple[V07JCell, ...]
    cell_count: int
    eligible_count: int
    ineligible_count: int
    selected_better_count: int
    selected_better_rate: float
    mean_ratio: float
    minimum_ratio: float
    maximum_ratio: float
    hardest_positive_cell: V07JCell | None
    easiest_failure_cell: V07JCell | None


def evaluate_v07j_surface() -> V07JSurface:
    cells = []
    for psi0, gamma, epsilon in product(
        V07J_PSI0_GRID,
        V07J_GAMMA_GRID,
        V07J_EPSILON_GRID,
    ):
        theta = _theta(psi0, gamma, epsilon)
        selected = _score_placement(
            V07G_SELECTED_PLACEMENT,
            theta=theta,
        )
        baseline = _score_placement(
            V07G_BASELINE_PLACEMENT,
            theta=theta,
        )
        ratio = selected.worst_dynamic_sd / baseline.worst_dynamic_sd
        eligible = bool(
            selected.conditioning_pass and baseline.conditioning_pass
        )
        cells.append(
            V07JCell(
                psi0=float(psi0),
                gamma=float(gamma),
                epsilon=float(epsilon),
                selected_worst_dynamic_sd=float(selected.worst_dynamic_sd),
                baseline_worst_dynamic_sd=float(baseline.worst_dynamic_sd),
                selected_to_baseline_ratio=float(ratio),
                selected_better=bool(ratio < 1.0),
                selected_conditioning_pass=bool(selected.conditioning_pass),
                baseline_conditioning_pass=bool(baseline.conditioning_pass),
                jointly_eligible=eligible,
                selected_condition_number=float(selected.condition_number),
                baseline_condition_number=float(baseline.condition_number),
            )
        )

    rows = tuple(cells)
    expected = (
        len(V07J_PSI0_GRID)
        * len(V07J_GAMMA_GRID)
        * len(V07J_EPSILON_GRID)
    )
    if len(rows) != expected or expected != 36:
        raise RuntimeError("v0.7j surface must contain exactly 36 cells")

    eligible = tuple(row for row in rows if row.jointly_eligible)
    if not eligible:
        raise RuntimeError("v0.7j surface has no jointly eligible cells")
    positive = tuple(row for row in eligible if row.selected_better)
    failures = tuple(row for row in eligible if not row.selected_better)
    hardest_positive = (
        max(positive, key=lambda row: row.selected_to_baseline_ratio)
        if positive
        else None
    )
    easiest_failure = (
        min(failures, key=lambda row: row.selected_to_baseline_ratio)
        if failures
        else None
    )
    ratios = tuple(row.selected_to_baseline_ratio for row in eligible)
    return V07JSurface(
        cells=rows,
        cell_count=len(rows),
        eligible_count=len(eligible),
        ineligible_count=len(rows) - len(eligible),
        selected_better_count=len(positive),
        selected_better_rate=len(positive) / len(eligible),
        mean_ratio=math.fsum(ratios) / len(ratios),
        minimum_ratio=min(ratios),
        maximum_ratio=max(ratios),
        hardest_positive_cell=hardest_positive,
        easiest_failure_cell=easiest_failure,
    )
