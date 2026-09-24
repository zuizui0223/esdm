"""Finite v0.6c identification frontier for static accessibility."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from esdm.observe import (
    AccessibilityCount,
    AccessiblePresenceOnly,
    EffortField,
)
from esdm.process import LinearAccessibility, LinearSuitability
from .evidence import diagnose_identification
from .v06a_fixture import (
    V06A_RECOVERY_TRUTH,
    build_v06a_joint_only_refusal,
)


V06C_GEOMETRIES = ("distinct", "aligned", "flat_access")
V06C_ACCESS_INTERCEPTS = (-2.0, 0.40, 2.0)
V06C_TARGETS = tuple(V06A_RECOVERY_TRUTH)

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
    "target_sd_threshold": 0.25,
    "fisher_ridge": 1e-10,
}


@dataclass(frozen=True, slots=True)
class V06CFrontierCell:
    geometry: str
    access_intercept: float
    joint_only: dict
    direct_calibrated: dict

    @property
    def joint_structural_count(self) -> int:
        return sum(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in self.joint_only.values()
        )

    @property
    def joint_practical_count(self) -> int:
        return sum(
            row.practical is not None and not row.practical.weak
            for row in self.joint_only.values()
        )

    @property
    def direct_structural_count(self) -> int:
        return sum(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in self.direct_calibrated.values()
        )

    @property
    def direct_practical_count(self) -> int:
        return sum(
            row.practical is not None and not row.practical.weak
            for row in self.direct_calibrated.values()
        )


@dataclass(frozen=True, slots=True)
class V06CFrontier:
    intercept_only_refused: bool
    intercept_only: dict
    cells: tuple[V06CFrontierCell, ...]


def _base_rows(n: int = 24):
    rows = []
    for index in range(n):
        habitat = (
            math.sin(2.0 * math.pi * index / 12.0)
            + 0.35 * math.cos(2.0 * math.pi * index / 5.0)
        )
        distance = (
            math.cos(2.0 * math.pi * index / 9.0)
            + 0.25 * math.sin(2.0 * math.pi * index / 7.0)
        )
        rows.append((float(habitat), float(distance)))
    return tuple(rows)


def _covariates(geometry: str):
    name = str(geometry)
    if name not in V06C_GEOMETRIES:
        raise ValueError("unknown v0.6c geometry")
    rows = _base_rows()
    spaces = tuple(f"s{index:02d}" for index in range(len(rows)))
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    covariates = {}
    for index, key in enumerate(grid.keys):
        habitat, distance = rows[index]
        if name == "aligned":
            distance = habitat
        elif name == "flat_access":
            distance = 0.0
        covariates[key] = {
            "habitat": habitat,
            "distance": distance,
        }
    return grid, covariates


def _models(geometry: str, access_intercept: float):
    grid, covariates = _covariates(geometry)
    processes = (
        LinearSuitability(
            covariates=("habitat",),
            intercept_parameter="suitability_intercept",
            coefficient_parameters={"habitat": "beta_habitat"},
        ),
        LinearAccessibility(
            covariates=("distance",),
            intercept_parameter="access_intercept",
            coefficient_parameters={"distance": "beta_distance"},
        ),
    )
    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    direct = AccessibilityCount(
        "access",
        effort=EffortField({key: 20.0 for key in grid.keys}),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    joint_only = Model(
        domain=grid,
        species={"sp": processes},
        streams=(joint,),
    )
    direct_calibrated = Model(
        domain=grid,
        species={"sp": processes},
        streams=(joint, direct),
    )
    joint_only.check_design()
    direct_calibrated.check_design()

    theta = {
        "sp": {
            "suitability_intercept": 0.30,
            "beta_habitat": 0.75,
            "access_intercept": float(access_intercept),
            "beta_distance": -1.10,
        }
    }
    return (
        joint_only,
        direct_calibrated,
        covariates,
        theta,
        {"joint": {}},
        {"joint": {}, "access": {}},
    )


def _diagnose(model, covariates, theta, theta_obs):
    return {
        target: diagnose_identification(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )
        for target in V06C_TARGETS
    }


def evaluate_v06c_frontier() -> V06CFrontier:
    refusal_model, refusal_cov, refusal_theta, refusal_obs = (
        build_v06a_joint_only_refusal()
    )
    intercept_only = {
        target: diagnose_identification(
            refusal_model,
            refusal_cov,
            theta=refusal_theta,
            theta_obs=refusal_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )
        for target in (
            "sp.suitability.suitability_intercept",
            "sp.accessibility.access_intercept",
        )
    }
    refused = all(
        row.structural.status is IdentificationStatus.NOT_IDENTIFIED
        for row in intercept_only.values()
    )

    cells = []
    for geometry in V06C_GEOMETRIES:
        for intercept in V06C_ACCESS_INTERCEPTS:
            (
                joint_only,
                direct_calibrated,
                covariates,
                theta,
                joint_obs,
                direct_obs,
            ) = _models(geometry, intercept)
            cells.append(
                V06CFrontierCell(
                    geometry=geometry,
                    access_intercept=float(intercept),
                    joint_only=_diagnose(
                        joint_only, covariates, theta, joint_obs
                    ),
                    direct_calibrated=_diagnose(
                        direct_calibrated, covariates, theta, direct_obs
                    ),
                )
            )
    return V06CFrontier(
        intercept_only_refused=refused,
        intercept_only=intercept_only,
        cells=tuple(cells),
    )
