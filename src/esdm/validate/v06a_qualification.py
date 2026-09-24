"""Pre-MCMC identification qualification for v0.6a."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import diagnose_identification
from .v06a_fixture import (
    V06A_RECOVERY_TRUTH,
    V06A_REFUSAL_TARGETS,
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
class V06AQualification:
    positive_structural_pass: bool
    positive_practical_pass: bool
    joint_only_refusal_pass: bool
    positive_evidence: dict
    refusal_evidence: dict


def _training_model(fixture):
    grid = Grid(
        space=fixture.train_spaces,
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def evaluate_v06a_identification() -> V06AQualification:
    fixture = build_v06a_fixture()
    model, covariates = _training_model(fixture)

    positive = {}
    for target in V06A_RECOVERY_TRUTH:
        positive[target] = diagnose_identification(
            model,
            covariates,
            theta=fixture.generating_theta,
            theta_obs=fixture.generating_theta_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    refusal_model, refusal_cov, refusal_theta, refusal_obs = (
        build_v06a_joint_only_refusal()
    )
    refusal = {}
    for target in V06A_REFUSAL_TARGETS:
        refusal[target] = diagnose_identification(
            refusal_model,
            refusal_cov,
            theta=refusal_theta,
            theta_obs=refusal_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    structural_pass = all(
        row.structural.status is IdentificationStatus.IDENTIFIED
        for row in positive.values()
    )
    practical_pass = all(
        row.practical is not None and not row.practical.weak
        for row in positive.values()
    )
    refusal_pass = all(
        row.structural.status is IdentificationStatus.NOT_IDENTIFIED
        for row in refusal.values()
    )
    return V06AQualification(
        positive_structural_pass=structural_pass,
        positive_practical_pass=practical_pass,
        joint_only_refusal_pass=refusal_pass,
        positive_evidence=positive,
        refusal_evidence=refusal,
    )
