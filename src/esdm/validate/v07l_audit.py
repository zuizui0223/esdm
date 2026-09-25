"""Fresh population cells for the v0.7l pilot-gated adaptation test."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import math

from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_selector import _score_placement, select_v07i_placement_from_theta


V07L_PSI0_GRID = (0.10, 0.20, 0.50, 0.80)
V07L_GAMMA_GRID = (0.15, 0.35, 0.55)
V07L_EPSILON_GRID = (0.05, 0.15, 0.30)
V07L_TRIGGER_RATIO = 0.80

# Exact truth cells already consumed by earlier confirmatory programmes on this grid.
V07L_EXCLUDED_CELLS = frozenset({
    (0.20, 0.35, 0.15),  # v0.7 source truth / v0.7i
    (0.20, 0.15, 0.05),  # v0.7k transfer-positive stress
    (0.80, 0.15, 0.30),  # v0.7k reversal stress
})


def _logit(probability: float) -> float:
    p = float(probability)
    return math.log(p / (1.0 - p))


def theta_for_cell(psi0: float, gamma: float, epsilon: float):
    return {
        "sp": {
            "alpha": 0.30,
            "psi0_logit": _logit(psi0),
            "gamma_logit": _logit(gamma),
            "epsilon_logit": _logit(epsilon),
        }
    }


@dataclass(frozen=True, slots=True)
class V07LAuditCell:
    psi0: float
    gamma: float
    epsilon: float
    local_oracle_placement: tuple[int, ...]
    local_oracle_worst_sd: float
    transferred_worst_sd: float
    oracle_to_transferred_ratio: float
    transferred_conditioning_pass: bool
    excluded_prior_truth: bool


@dataclass(frozen=True, slots=True)
class V07LAudit:
    eligible_fresh_cells: int
    high_headroom: tuple[V07LAuditCell, ...]
    low_headroom: tuple[V07LAuditCell, ...]
    trigger_ratio: float
    all_fresh_cells: tuple[V07LAuditCell, ...]


def evaluate_v07l_audit() -> V07LAudit:
    rows = []
    for psi0, gamma, epsilon in product(
        V07L_PSI0_GRID,
        V07L_GAMMA_GRID,
        V07L_EPSILON_GRID,
    ):
        theta = theta_for_cell(psi0, gamma, epsilon)
        local = select_v07i_placement_from_theta(theta).selected
        transferred = _score_placement(
            V07G_SELECTED_PLACEMENT,
            theta=theta,
        )
        key = (float(psi0), float(gamma), float(epsilon))
        rows.append(
            V07LAuditCell(
                psi0=float(psi0),
                gamma=float(gamma),
                epsilon=float(epsilon),
                local_oracle_placement=local.placement,
                local_oracle_worst_sd=float(local.worst_dynamic_sd),
                transferred_worst_sd=float(transferred.worst_dynamic_sd),
                oracle_to_transferred_ratio=float(
                    local.worst_dynamic_sd / transferred.worst_dynamic_sd
                ),
                transferred_conditioning_pass=bool(
                    transferred.conditioning_pass
                ),
                excluded_prior_truth=key in V07L_EXCLUDED_CELLS,
            )
        )

    if len(rows) != 36:
        raise RuntimeError("v0.7l audit must evaluate exactly 36 grid cells")

    fresh = tuple(
        row for row in rows
        if row.transferred_conditioning_pass
        and not row.excluded_prior_truth
    )
    if len(fresh) < 4:
        raise RuntimeError("v0.7l audit has too few eligible fresh cells")

    ordered = tuple(
        sorted(
            fresh,
            key=lambda row: (
                row.oracle_to_transferred_ratio,
                row.psi0,
                row.gamma,
                row.epsilon,
            ),
        )
    )
    high = ordered[:2]
    low = ordered[-2:]

    if max(row.oracle_to_transferred_ratio for row in high) > V07L_TRIGGER_RATIO:
        raise RuntimeError(
            "v0.7l high-headroom cells do not clear the frozen trigger ratio"
        )
    if min(row.oracle_to_transferred_ratio for row in low) < 0.90:
        raise RuntimeError(
            "v0.7l low-headroom cells are not sufficiently near the transferred design"
        )

    return V07LAudit(
        eligible_fresh_cells=len(fresh),
        high_headroom=high,
        low_headroom=low,
        trigger_ratio=V07L_TRIGGER_RATIO,
        all_fresh_cells=ordered,
    )
