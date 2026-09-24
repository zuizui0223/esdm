"""Exact-JAX qualification for v0.6c budget-matched evidence."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v06a_fixture import V06A_RECOVERY_TRUTH
from .v06c_fixture import (
    V06C_ACCESS_TARGETS,
    build_v06c_fixture,
    v06c_condition_model,
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
class V06CQualification:
    relative_budget_error: float
    expected_direct_aux_count: float
    expected_matched_aux_count: float
    direct_evidence: dict
    matched_evidence: dict
    access_sd_proxy_ratios: dict

    @property
    def direct_all_structural(self) -> bool:
        return all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in self.direct_evidence.values()
        )

    @property
    def direct_all_practical(self) -> bool:
        return all(
            row.practical is not None and not row.practical.weak
            for row in self.direct_evidence.values()
        )

    @property
    def matched_all_structural(self) -> bool:
        return all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for row in self.matched_evidence.values()
        )


def evaluate_v06c_qualification() -> V06CQualification:
    fixture = build_v06c_fixture()
    direct_model, direct_cov = v06c_condition_model(
        fixture, "direct", fixture.train_spaces
    )
    matched_model, matched_cov = v06c_condition_model(
        fixture, "matched_joint", fixture.train_spaces
    )

    direct = {}
    matched = {}
    for target in V06A_RECOVERY_TRUTH:
        direct[target] = diagnose_identification(
            direct_model,
            direct_cov,
            theta=fixture.generating_theta,
            theta_obs={"base_joint": {}, "direct_access": {}},
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )
        matched[target] = diagnose_identification(
            matched_model,
            matched_cov,
            theta=fixture.generating_theta,
            theta_obs={"base_joint": {}, "matched_joint": {}},
            target=target,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )

    ratios = {}
    for target in V06C_ACCESS_TARGETS:
        direct_sd = direct[target].practical.target_sd_proxy
        matched_sd = matched[target].practical.target_sd_proxy
        ratios[target] = float(direct_sd) / float(matched_sd)

    return V06CQualification(
        relative_budget_error=fixture.relative_budget_error,
        expected_direct_aux_count=fixture.expected_direct_aux_count,
        expected_matched_aux_count=fixture.expected_matched_aux_count,
        direct_evidence=direct,
        matched_evidence=matched,
        access_sd_proxy_ratios=ratios,
    )
