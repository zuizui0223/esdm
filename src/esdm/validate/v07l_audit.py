"""Fresh population cells for the v0.7l pilot-gated adaptation test."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from functools import lru_cache
import math

import numpy as np

from esdm.identify.design_rank import design_jacobian_diagnostic
from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07b_fixture import (
    V07B_DIRECT_EFFORT,
    V07B_TRUTH,
    build_v07b_fixture,
)
from .v07g_fixture import V07G_DYNAMIC_TARGETS, V07G_SELECTED_PLACEMENT


V07L_PSI0_GRID = (0.05, 0.10, 0.20, 0.50, 0.80, 0.95)
V07L_GAMMA_GRID = (0.05, 0.15, 0.35, 0.55, 0.75)
V07L_EPSILON_GRID = (0.02, 0.05, 0.15, 0.30, 0.50)
V07L_TRIGGER_RATIO = 0.80
V07L_LOW_HEADROOM_MIN_RATIO = 0.95
V07L_LOW_HEADROOM_MAX_SD = 0.25

# Exact truth cells already consumed by earlier confirmatory programmes on this grid.
V07L_EXCLUDED_CELLS = frozenset({
    (0.20, 0.35, 0.15),  # v0.7 source truth / v0.7i
    (0.20, 0.15, 0.05),  # v0.7k transfer-positive stress
    (0.80, 0.15, 0.30),  # v0.7k reversal stress
})

_RTOL = 1e-8
_ATOL = 1e-10
_RELATIVE_MIN_THRESHOLD = 1e-3
_CONDITION_THRESHOLD = 1e3
_FISHER_RIDGE = 1e-10


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
class _PlacementScore:
    placement: tuple[int, ...]
    worst_dynamic_sd: float
    conditioning_pass: bool


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
    local_eligible: bool
    excluded_prior_truth: bool


@dataclass(frozen=True, slots=True)
class V07LAudit:
    eligible_fresh_cells: int
    high_headroom: tuple[V07LAuditCell, ...]
    low_headroom: tuple[V07LAuditCell, ...]
    trigger_ratio: float
    low_headroom_min_ratio: float
    low_headroom_max_sd: float
    all_fresh_cells: tuple[V07LAuditCell, ...]


def _full_direct_diagnostic(theta):
    source = build_v07b_fixture()
    joint = next(
        stream for stream in source.training_model.streams
        if stream.name == "joint"
    )
    direct = OccupancyCount(
        "occupancy_calibration",
        effort=EffortField({
            key: float(V07B_DIRECT_EFFORT)
            for key in source.joint_train_keys
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint, direct),
    )
    model.check_design()
    diagnostic = design_jacobian_diagnostic(
        model,
        source.covariates,
        theta=theta,
        theta_obs={"joint": {}, "occupancy_calibration": {}},
        target=next(iter(V07B_TRUTH)),
        rtol=_RTOL,
        atol=_ATOL,
    )
    expected_rows = 2 * len(source.joint_train_keys)
    if diagnostic.observation_dimension != expected_rows:
        raise RuntimeError(
            "v0.7l full-direct diagnostic row structure changed"
        )
    return source, diagnostic


def _relative_rank(singular_values):
    if len(singular_values) == 0:
        return 0
    cutoff = max(_ATOL, _RTOL * float(singular_values[0]))
    return int(sum(float(value) > cutoff for value in singular_values))


def _placement_scores(theta):
    source, diagnostic = _full_direct_diagnostic(theta)
    n = len(source.joint_train_keys)
    jac = np.asarray(diagnostic.jacobian, dtype=float)
    expected = np.asarray(diagnostic.expected_rates, dtype=float)

    joint_jac = jac[:n]
    direct_jac = jac[n:]
    joint_expected = expected[:n]
    direct_expected = expected[n:]
    if direct_jac.shape[0] != n:
        raise RuntimeError("v0.7l direct Jacobian row count changed")

    site_names = tuple(diagnostic.site_names)
    target_indices = {
        target: site_names.index(target)
        for target in V07B_TRUTH
    }
    parameter_count = len(site_names)
    rows = []

    for placement in combinations(range(1, n + 1), 4):
        indices = np.asarray([day - 1 for day in placement], dtype=int)
        active_jac = np.vstack((joint_jac, direct_jac[indices]))
        active_expected = np.concatenate(
            (joint_expected, direct_expected[indices])
        )

        singular = np.linalg.svd(active_jac, compute_uv=False)
        full_rank = _relative_rank(singular)
        if full_rank < parameter_count or len(singular) == 0:
            relative_min = 0.0
            condition = math.inf
        else:
            largest = float(singular[0])
            smallest = float(singular[-1])
            relative_min = 0.0 if largest <= 0.0 else smallest / largest
            condition = math.inf if smallest <= 0.0 else largest / smallest

        conditioning_pass = (
            full_rank == parameter_count
            and relative_min >= _RELATIVE_MIN_THRESHOLD
            and condition <= _CONDITION_THRESHOLD
        )

        fisher = active_jac.T @ (
            active_expected[:, None] * active_jac
        )
        diagonal = np.diag(fisher)
        scale = max(1.0, float(np.max(diagonal))) if diagonal.size else 1.0
        covariance = np.linalg.inv(
            fisher
            + _FISHER_RIDGE * scale * np.eye(parameter_count)
        )
        sds = {
            target: math.sqrt(
                max(0.0, float(covariance[index, index]))
            )
            for target, index in target_indices.items()
        }
        rows.append(
            _PlacementScore(
                placement=tuple(int(day) for day in placement),
                worst_dynamic_sd=max(
                    sds[target] for target in V07G_DYNAMIC_TARGETS
                ),
                conditioning_pass=bool(conditioning_pass),
            )
        )
    if len(rows) != 70:
        raise RuntimeError("v0.7l must score exactly 70 placements")
    return tuple(rows)


def score_v07l_cell(psi0: float, gamma: float, epsilon: float) -> V07LAuditCell:
    theta = theta_for_cell(psi0, gamma, epsilon)
    scores = _placement_scores(theta)
    eligible = tuple(row for row in scores if row.conditioning_pass)
    transferred = next(
        row for row in scores
        if row.placement == V07G_SELECTED_PLACEMENT
    )
    key = (float(psi0), float(gamma), float(epsilon))
    if eligible:
        local = min(
            eligible,
            key=lambda row: (row.worst_dynamic_sd, row.placement),
        )
        local_placement = local.placement
        local_sd = float(local.worst_dynamic_sd)
        ratio = float(local.worst_dynamic_sd / transferred.worst_dynamic_sd)
    else:
        local_placement = ()
        local_sd = math.inf
        ratio = math.inf
    return V07LAuditCell(
        psi0=float(psi0),
        gamma=float(gamma),
        epsilon=float(epsilon),
        local_oracle_placement=local_placement,
        local_oracle_worst_sd=local_sd,
        transferred_worst_sd=float(transferred.worst_dynamic_sd),
        oracle_to_transferred_ratio=ratio,
        transferred_conditioning_pass=bool(
            transferred.conditioning_pass
        ),
        local_eligible=bool(eligible),
        excluded_prior_truth=key in V07L_EXCLUDED_CELLS,
    )


@lru_cache(maxsize=1)
def evaluate_v07l_audit() -> V07LAudit:
    rows = tuple(
        score_v07l_cell(psi0, gamma, epsilon)
        for psi0, gamma, epsilon in product(
            V07L_PSI0_GRID,
            V07L_GAMMA_GRID,
            V07L_EPSILON_GRID,
        )
    )
    expected_cells = (
        len(V07L_PSI0_GRID)
        * len(V07L_GAMMA_GRID)
        * len(V07L_EPSILON_GRID)
    )
    if len(rows) != expected_cells or expected_cells != 150:
        raise RuntimeError("v0.7l audit must evaluate exactly 150 grid cells")

    fresh = tuple(
        row for row in rows
        if row.transferred_conditioning_pass
        and row.local_eligible
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
    low_candidates = tuple(
        row
        for row in fresh
        if row.oracle_to_transferred_ratio >= V07L_LOW_HEADROOM_MIN_RATIO
        and row.transferred_worst_sd <= V07L_LOW_HEADROOM_MAX_SD
    )
    low = tuple(
        sorted(
            low_candidates,
            key=lambda row: (
                -row.oracle_to_transferred_ratio,
                row.transferred_worst_sd,
                row.psi0,
                row.gamma,
                row.epsilon,
            ),
        )[:2]
    )

    if max(row.oracle_to_transferred_ratio for row in high) > V07L_TRIGGER_RATIO:
        raise RuntimeError(
            "v0.7l expanded grid lacks two high-headroom fresh cells"
        )
    if len(low) != 2:
        raise RuntimeError(
            "v0.7l expanded grid lacks two low-headroom precise fresh cells"
        )

    return V07LAudit(
        eligible_fresh_cells=len(fresh),
        high_headroom=high,
        low_headroom=low,
        trigger_ratio=V07L_TRIGGER_RATIO,
        low_headroom_min_ratio=V07L_LOW_HEADROOM_MIN_RATIO,
        low_headroom_max_sd=V07L_LOW_HEADROOM_MAX_SD,
        all_fresh_cells=ordered,
    )
