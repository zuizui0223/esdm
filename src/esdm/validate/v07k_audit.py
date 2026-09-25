"""Deterministic local re-pilot potential under v0.7j population shifts."""

from __future__ import annotations

from dataclasses import dataclass

from .v07g_fixture import (
    V07G_BASELINE_PLACEMENT,
    V07G_SELECTED_PLACEMENT,
)
from .v07i_selector import (
    _score_placement,
    select_v07i_placement_from_theta,
)
from .v07j_confirm import (
    V07K_WORLDS,
    theta_for_v07k_world,
)


@dataclass(frozen=True, slots=True)
class V07KWorldAudit:
    world: str
    local_oracle_placement: tuple[int, ...]
    local_oracle_worst_dynamic_sd: float
    transferred_worst_dynamic_sd: float
    baseline_worst_dynamic_sd: float
    local_oracle_to_transferred_ratio: float
    local_oracle_to_baseline_ratio: float
    transferred_to_baseline_ratio: float
    placements_evaluated: int


@dataclass(frozen=True, slots=True)
class V07KAudit:
    worlds: dict


def evaluate_v07k_local_oracle_audit() -> V07KAudit:
    rows = {}
    for world in V07K_WORLDS:
        theta = theta_for_v07k_world(world)
        selection = select_v07i_placement_from_theta(theta)
        transferred = _score_placement(
            V07G_SELECTED_PLACEMENT,
            theta=theta,
        )
        baseline = _score_placement(
            V07G_BASELINE_PLACEMENT,
            theta=theta,
        )
        selected = selection.selected
        rows[world] = V07KWorldAudit(
            world=world,
            local_oracle_placement=selected.placement,
            local_oracle_worst_dynamic_sd=selected.worst_dynamic_sd,
            transferred_worst_dynamic_sd=transferred.worst_dynamic_sd,
            baseline_worst_dynamic_sd=baseline.worst_dynamic_sd,
            local_oracle_to_transferred_ratio=(
                selected.worst_dynamic_sd / transferred.worst_dynamic_sd
            ),
            local_oracle_to_baseline_ratio=(
                selected.worst_dynamic_sd / baseline.worst_dynamic_sd
            ),
            transferred_to_baseline_ratio=(
                transferred.worst_dynamic_sd / baseline.worst_dynamic_sd
            ),
            placements_evaluated=selection.placements_evaluated,
        )
    return V07KAudit(worlds=rows)
