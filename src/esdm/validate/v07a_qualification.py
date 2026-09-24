"""Prospective exact-identification gate for v0.7a."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v07a_fixture import V07A_TRUTH, build_v07a_fixture


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
class V07AQualification:
    positive_structural_pass: bool
    positive_practical_pass: bool
    joint_only_refusal_pass: bool
    positive_evidence: dict
    refusal_evidence: dict


def evaluate_v07a_identification() -> V07AQualification:
    fixture = build_v07a_fixture()
    positive = {}
    refusal = {}

    for target in V07A_TRUTH:
        positive[target] = diagnose_identification(
            fixture.positive_model,
            fixture.covariates,
            theta=fixture.theta,
            theta_obs=fixture.theta_obs_positive,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )
        refusal[target] = diagnose_identification(
            fixture.refusal_model,
            fixture.covariates,
            theta=fixture.theta,
            theta_obs=fixture.theta_obs_refusal,
            target=target,
            practical=False,
            structural_kwargs=_STRUCTURAL,
        )

    return V07AQualification(
        positive_structural_pass=all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in positive.values()
        ),
        positive_practical_pass=all(
            row.practical is not None and not row.practical.weak
            for row in positive.values()
        ),
        joint_only_refusal_pass=all(
            row.structural.status is IdentificationStatus.NOT_IDENTIFIED
            for row in refusal.values()
        ),
        positive_evidence=positive,
        refusal_evidence=refusal,
    )
