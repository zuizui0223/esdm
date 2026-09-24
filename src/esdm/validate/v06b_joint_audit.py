"""Deterministic v0.6b audit of joint-only suitability/accessibility identification."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import diagnose_identification
from .v06a_fixture import (
    V06A_RECOVERY_TRUTH,
    build_v06a_fixture,
    build_v06a_joint_only_refusal,
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
    "target_sd_threshold": 0.25,
    "fisher_ridge": 1e-10,
}


@dataclass(frozen=True, slots=True)
class V06BJointAudit:
    intercept_only: dict
    structured_joint_only: dict

    @property
    def intercept_only_refused(self) -> bool:
        return all(
            row.structural.status is IdentificationStatus.NOT_IDENTIFIED
            for row in self.intercept_only.values()
        )

    @property
    def structured_all_structural(self) -> bool:
        return all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in self.structured_joint_only.values()
        )

    @property
    def structured_all_practical(self) -> bool:
        return all(
            row.practical is not None and not row.practical.weak
            for row in self.structured_joint_only.values()
        )


def _v06a_training_joint_only():
    fixture = build_v06a_fixture()
    grid = Grid(
        space=fixture.train_spaces,
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    joint = next(
        stream for stream in fixture.model.streams
        if stream.name == "joint"
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=(joint,),
    )
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates, fixture.generating_theta, {"joint": {}}


def evaluate_v06b_joint_audit() -> V06BJointAudit:
    refusal_model, refusal_cov, refusal_theta, refusal_obs = (
        build_v06a_joint_only_refusal()
    )
    intercept_only = {}
    for target in (
        "sp.suitability.suitability_intercept",
        "sp.accessibility.access_intercept",
    ):
        intercept_only[target] = diagnose_identification(
            refusal_model,
            refusal_cov,
            theta=refusal_theta,
            theta_obs=refusal_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    model, covariates, theta, theta_obs = _v06a_training_joint_only()
    structured = {}
    for target in V06A_RECOVERY_TRUTH:
        structured[target] = diagnose_identification(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    return V06BJointAudit(
        intercept_only=intercept_only,
        structured_joint_only=structured,
    )
