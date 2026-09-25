"""Pre-outcome identification qualification for v0.7c matched models."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v07b_qualification import evaluate_v07b_identification
from .v07c_fixture import V07C_STATIC_NOMINAL, build_v07c_fixture


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
class V07CQualification:
    dynamic_structural_pass: bool
    dynamic_practical_pass: bool
    static_structural_pass: bool
    static_practical_pass: bool
    static_evidence: dict


def evaluate_v07c_identification() -> V07CQualification:
    dynamic = evaluate_v07b_identification()
    fixture = build_v07c_fixture()
    static = {}

    for target in V07C_STATIC_NOMINAL:
        static[target] = diagnose_identification(
            fixture.static_training_model,
            fixture.covariates,
            theta=fixture.static_nominal_theta,
            theta_obs=fixture.generating_theta_obs,
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    return V07CQualification(
        dynamic_structural_pass=dynamic.positive_structural_pass,
        dynamic_practical_pass=dynamic.positive_practical_pass,
        static_structural_pass=all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in static.values()
        ),
        static_practical_pass=all(
            row.practical is not None and not row.practical.weak
            for row in static.values()
        ),
        static_evidence=static,
    )
