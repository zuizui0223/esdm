"""Frozen v0.7m absolute-adequacy-first adaptation policy."""
from __future__ import annotations

from dataclasses import dataclass

from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_selector import _score_placement, select_v07i_placement_from_theta
from .v07l_audit import evaluate_v07l_candidate_surface


V07M_ABSOLUTE_SD_THRESHOLD = 0.35
V07M_RELATIVE_HEADROOM_THRESHOLD = 0.80

V07M_ROLE_CELL_IDS = {
    "adaptive_large_headroom": "psi85_gam45_eps38",
    "adaptive_absolute_rescue": "psi35_gam25_eps22",
    "transfer_adequate": "psi35_gam25_eps08",
    "abstain_inadequate": "psi65_gam45_eps08",
}
V07M_EXPECTED_ACTIONS = {
    "adaptive_large_headroom": "adaptive",
    "adaptive_absolute_rescue": "adaptive",
    "transfer_adequate": "transferred",
    "abstain_inadequate": "abstain",
}


@dataclass(frozen=True, slots=True)
class V07MPolicyDecision:
    action: str
    adaptive_placement: tuple[int, ...]
    adaptive_worst_dynamic_sd: float
    transferred_worst_dynamic_sd: float
    adaptive_to_transferred_ratio: float
    reason: str


def decide_v07m_from_scores(
    *,
    adaptive_placement,
    adaptive_worst_dynamic_sd: float,
    transferred_worst_dynamic_sd: float,
) -> V07MPolicyDecision:
    placement = tuple(int(day) for day in adaptive_placement)
    adaptive_sd = float(adaptive_worst_dynamic_sd)
    transferred_sd = float(transferred_worst_dynamic_sd)
    if adaptive_sd <= 0.0 or transferred_sd <= 0.0:
        raise ValueError("v0.7m predicted SDs must be positive")
    ratio = adaptive_sd / transferred_sd

    if adaptive_sd > V07M_ABSOLUTE_SD_THRESHOLD:
        action = "abstain"
        reason = "no_placement_meets_absolute_precision"
    elif transferred_sd > V07M_ABSOLUTE_SD_THRESHOLD:
        action = "adaptive"
        reason = "adaptive_restores_absolute_precision"
    elif ratio <= V07M_RELATIVE_HEADROOM_THRESHOLD:
        action = "adaptive"
        reason = "material_relative_headroom"
    else:
        action = "transferred"
        reason = "transferred_is_absolutely_adequate_and_relative_headroom_is_small"

    return V07MPolicyDecision(
        action=action,
        adaptive_placement=placement,
        adaptive_worst_dynamic_sd=adaptive_sd,
        transferred_worst_dynamic_sd=transferred_sd,
        adaptive_to_transferred_ratio=ratio,
        reason=reason,
    )


def decide_v07m_from_theta(theta) -> V07MPolicyDecision:
    selected = select_v07i_placement_from_theta(theta).selected
    transferred = _score_placement(
        V07G_SELECTED_PLACEMENT,
        theta=theta,
    )
    return decide_v07m_from_scores(
        adaptive_placement=selected.placement,
        adaptive_worst_dynamic_sd=selected.worst_dynamic_sd,
        transferred_worst_dynamic_sd=transferred.worst_dynamic_sd,
    )


def frozen_v07m_role_cells() -> dict[str, object]:
    cells = {
        row.cell_id: row
        for row in evaluate_v07l_candidate_surface()
    }
    selected = {}
    for role, cell_id in V07M_ROLE_CELL_IDS.items():
        row = cells[cell_id]
        if not row.eligible:
            raise RuntimeError(f"v0.7m role {role!r} is not design-eligible")
        decision = decide_v07m_from_scores(
            adaptive_placement=row.local_oracle_placement,
            adaptive_worst_dynamic_sd=row.local_oracle_worst_dynamic_sd,
            transferred_worst_dynamic_sd=row.transferred_worst_dynamic_sd,
        )
        if decision.action != V07M_EXPECTED_ACTIONS[role]:
            raise RuntimeError(
                f"v0.7m role {role!r} expected {V07M_EXPECTED_ACTIONS[role]!r}, "
                f"observed {decision.action!r}"
            )
        selected[role] = {
            "cell": row,
            "decision": decision,
        }
    return selected
