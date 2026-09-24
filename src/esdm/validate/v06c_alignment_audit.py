"""v0.6c deterministic habitat-accessibility covariate-alignment stress."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from esdm.observe import AccessibilityCount, AccessiblePresenceOnly, EffortField
from esdm.process import LinearAccessibility, LinearSuitability
from .evidence import diagnose_identification
from .v06a_fixture import V06A_RECOVERY_TRUTH, _covariate_rows


V06C_ALIGNMENTS = (0.0, 0.5, 0.9, 0.99)

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
class V06CDesignAudit:
    alignment: float
    empirical_correlation: float
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
class V06CAlignmentAudit:
    rows: tuple[V06CDesignAudit, ...]

    @property
    def direct_all_practical(self) -> bool:
        return all(row.direct_practical_count == 4 for row in self.rows)

    @property
    def high_alignment_joint_accessibility_weak(self) -> bool:
        row = self.rows[-1]
        for target in (
            "sp.accessibility.access_intercept",
            "sp.accessibility.beta_distance",
        ):
            evidence = row.joint_only[target]
            if evidence.practical is None or not evidence.practical.weak:
                return False
        return True


def _standardize(values):
    values = tuple(float(value) for value in values)
    mean = math.fsum(values) / len(values)
    centered = tuple(value - mean for value in values)
    scale = math.sqrt(
        math.fsum(value * value for value in centered) / len(centered)
    )
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("cannot standardize constant vector")
    return tuple(value / scale for value in centered)


def _dot(left, right):
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _aligned_covariates(alignment: float):
    rho = float(alignment)
    if rho < 0.0 or rho >= 1.0:
        raise ValueError("alignment must be in [0,1)")
    rows = _covariate_rows(24)
    habitat = _standardize(row["habitat"] for row in rows)
    raw_distance = _standardize(row["distance"] for row in rows)

    projection = _dot(raw_distance, habitat) / _dot(habitat, habitat)
    residual = tuple(
        d - projection * h
        for d, h in zip(raw_distance, habitat, strict=True)
    )
    orthogonal = _standardize(residual)

    distance = tuple(
        rho * h + math.sqrt(1.0 - rho * rho) * z
        for h, z in zip(habitat, orthogonal, strict=True)
    )
    distance = _standardize(distance)
    correlation = _dot(habitat, distance) / len(habitat)

    spaces = tuple(f"c{index:02d}" for index in range(24))
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    covariates = {
        key: {
            "habitat": habitat[index],
            "distance": distance[index],
        }
        for index, key in enumerate(grid.keys)
    }
    return grid, covariates, float(correlation)


def _models(alignment: float):
    grid, covariates, correlation = _aligned_covariates(alignment)
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
    joint_only = Model(grid, {"sp": processes}, (joint,))
    calibrated = Model(grid, {"sp": processes}, (joint, direct))
    joint_only.check_design()
    calibrated.check_design()
    theta = {
        "sp": {
            "suitability_intercept": 0.30,
            "beta_habitat": 0.75,
            "access_intercept": 0.40,
            "beta_distance": -1.10,
        }
    }
    return (
        joint_only,
        calibrated,
        covariates,
        theta,
        {"joint": {}},
        {"joint": {}, "access": {}},
        correlation,
    )


def evaluate_v06c_alignment_audit() -> V06CAlignmentAudit:
    rows = []
    for alignment in V06C_ALIGNMENTS:
        (
            joint_only,
            calibrated,
            covariates,
            theta,
            joint_obs,
            direct_obs,
            correlation,
        ) = _models(alignment)

        joint = {}
        direct = {}
        for target in V06A_RECOVERY_TRUTH:
            joint[target] = diagnose_identification(
                joint_only,
                covariates,
                theta=theta,
                theta_obs=joint_obs,
                target=target,
                practical=True,
                structural_kwargs=_STRUCTURAL,
                practical_kwargs=_PRACTICAL,
            )
            direct[target] = diagnose_identification(
                calibrated,
                covariates,
                theta=theta,
                theta_obs=direct_obs,
                target=target,
                practical=True,
                structural_kwargs=_STRUCTURAL,
                practical_kwargs=_PRACTICAL,
            )
        rows.append(
            V06CDesignAudit(
                alignment=float(alignment),
                empirical_correlation=correlation,
                joint_only=joint,
                direct_calibrated=direct,
            )
        )
    return V06CAlignmentAudit(tuple(rows))
