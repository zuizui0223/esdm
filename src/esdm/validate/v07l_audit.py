"""Deterministic fresh-world audit for v0.7l selective local adaptation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from itertools import product
import math

from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_selector import _score_placement, select_v07i_placement_from_theta


V07L_TRIGGER_RATIO = 0.80
V07L_ALPHA = 0.30
V07L_PSI0_GRID = (0.15, 0.35, 0.65, 0.85)
V07L_GAMMA_GRID = (0.25, 0.45, 0.65)
V07L_EPSILON_GRID = (0.08, 0.22, 0.38)


def _logit(probability: float) -> float:
    p = float(probability)
    if not 0.0 < p < 1.0:
        raise ValueError("v0.7l probabilities must lie strictly between zero and one")
    return math.log(p / (1.0 - p))


def theta_from_probabilities(
    *,
    psi0: float,
    gamma: float,
    epsilon: float,
) -> dict:
    return {
        "sp": {
            "alpha": float(V07L_ALPHA),
            "psi0_logit": _logit(float(psi0)),
            "gamma_logit": _logit(float(gamma)),
            "epsilon_logit": _logit(float(epsilon)),
        }
    }


@dataclass(frozen=True, slots=True)
class V07LAuditCell:
    cell_id: str
    psi0: float
    gamma: float
    epsilon: float
    local_oracle_placement: tuple[int, ...]
    local_oracle_worst_dynamic_sd: float
    transferred_worst_dynamic_sd: float
    local_oracle_to_transferred_ratio: float
    transferred_structural_pass: bool
    transferred_conditioning_pass: bool
    eligible: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class V07LAudit:
    trigger_ratio: float
    cells: tuple[V07LAuditCell, ...]
    selected_worlds: dict[str, V07LAuditCell]

    def as_dict(self) -> dict[str, object]:
        return {
            "trigger_ratio": self.trigger_ratio,
            "cells": [row.as_dict() for row in self.cells],
            "selected_worlds": {
                role: row.as_dict()
                for role, row in self.selected_worlds.items()
            },
        }


def _cell_id(psi0: float, gamma: float, epsilon: float) -> str:
    return (
        f"psi{int(round(100 * psi0)):02d}_"
        f"gam{int(round(100 * gamma)):02d}_"
        f"eps{int(round(100 * epsilon)):02d}"
    )


@lru_cache(maxsize=1)
def evaluate_v07l_candidate_surface() -> tuple[V07LAuditCell, ...]:
    rows = []
    for psi0, gamma, epsilon in product(
        V07L_PSI0_GRID,
        V07L_GAMMA_GRID,
        V07L_EPSILON_GRID,
    ):
        theta = theta_from_probabilities(
            psi0=psi0,
            gamma=gamma,
            epsilon=epsilon,
        )
        selected = select_v07i_placement_from_theta(theta).selected
        transferred = _score_placement(
            V07G_SELECTED_PLACEMENT,
            theta=theta,
        )
        eligible = bool(
            transferred.structural_pass
            and transferred.conditioning_pass
            and selected.structural_pass
            and selected.conditioning_pass
        )
        ratio = (
            selected.worst_dynamic_sd / transferred.worst_dynamic_sd
            if eligible
            else math.inf
        )
        rows.append(
            V07LAuditCell(
                cell_id=_cell_id(psi0, gamma, epsilon),
                psi0=float(psi0),
                gamma=float(gamma),
                epsilon=float(epsilon),
                local_oracle_placement=tuple(selected.placement),
                local_oracle_worst_dynamic_sd=float(selected.worst_dynamic_sd),
                transferred_worst_dynamic_sd=float(transferred.worst_dynamic_sd),
                local_oracle_to_transferred_ratio=float(ratio),
                transferred_structural_pass=bool(transferred.structural_pass),
                transferred_conditioning_pass=bool(
                    transferred.conditioning_pass
                ),
                eligible=eligible,
            )
        )
    if len(rows) != 36:
        raise RuntimeError("v0.7l fresh candidate surface must contain 36 cells")
    return tuple(rows)


def select_v07l_confirmatory_worlds(
    cells: tuple[V07LAuditCell, ...],
) -> dict[str, V07LAuditCell]:
    eligible = tuple(row for row in cells if row.eligible)
    if len(eligible) < 4:
        raise RuntimeError("v0.7l requires at least four eligible candidate worlds")

    below = sorted(
        (row for row in eligible if row.local_oracle_to_transferred_ratio <= V07L_TRIGGER_RATIO),
        key=lambda row: (
            row.local_oracle_to_transferred_ratio,
            row.cell_id,
        ),
    )
    above = sorted(
        (row for row in eligible if row.local_oracle_to_transferred_ratio > V07L_TRIGGER_RATIO),
        key=lambda row: (
            row.local_oracle_to_transferred_ratio,
            row.cell_id,
        ),
    )
    if len(below) < 2 or len(above) < 2:
        raise RuntimeError(
            "v0.7l fresh surface must provide >=2 worlds on each side of the trigger"
        )

    strong = below[0]
    threshold_below = min(
        (row for row in below if row.cell_id != strong.cell_id),
        key=lambda row: (
            V07L_TRIGGER_RATIO - row.local_oracle_to_transferred_ratio,
            row.cell_id,
        ),
    )
    threshold_above = min(
        above,
        key=lambda row: (
            row.local_oracle_to_transferred_ratio - V07L_TRIGGER_RATIO,
            row.cell_id,
        ),
    )
    negligible = max(
        (row for row in above if row.cell_id != threshold_above.cell_id),
        key=lambda row: (
            row.local_oracle_to_transferred_ratio,
            row.cell_id,
        ),
    )

    selected = {
        "strong_headroom": strong,
        "threshold_below": threshold_below,
        "threshold_above": threshold_above,
        "negligible_headroom": negligible,
    }
    ids = [row.cell_id for row in selected.values()]
    if len(ids) != len(set(ids)):
        raise RuntimeError("v0.7l selected worlds must be unique")
    return selected


@lru_cache(maxsize=1)
def evaluate_v07l_audit() -> V07LAudit:
    cells = evaluate_v07l_candidate_surface()
    selected = select_v07l_confirmatory_worlds(cells)
    return V07LAudit(
        trigger_ratio=V07L_TRIGGER_RATIO,
        cells=cells,
        selected_worlds=selected,
    )
