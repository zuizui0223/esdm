"""Identification-only gate for v0.5b source perturbation design."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v05a_directed import V05A_TARGET
from .v05a_run import _subset_model
from .v05b_perturbation import build_v05b_fixture


_STRUCTURAL = {"method": "jax", "rtol": 1e-8, "atol": 1e-10}
_PRACTICAL = {
    "rtol": 1e-8,
    "atol": 1e-10,
    "relative_singular_value_threshold": 1e-3,
    "condition_number_threshold": 1e3,
    "target_sd_threshold": 0.25,
    "fisher_ridge": 1e-10,
}


@dataclass(frozen=True, slots=True)
class V05BIdentificationSummary:
    directed_structural: bool
    directed_practical: bool
    null_structural: bool
    null_practical: bool
    directed_target_sd: float
    null_target_sd: float


@dataclass(frozen=True, slots=True)
class V05BGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05BDecision:
    passed: bool
    checks: tuple[V05BGateCheck, ...]


def evaluate_v05b_identification(source_csv_text: str) -> V05BIdentificationSummary:
    rows = {}
    for world in ("directed_positive", "interaction_null"):
        fixture = build_v05b_fixture(source_csv_text, world=world)
        model, covariates = _subset_model(
            fixture, fixture.train_spaces, knockout=False
        )
        evidence = diagnose_identification(
            model,
            covariates,
            theta=fixture.generating_theta,
            theta_obs=fixture.generating_theta_obs,
            target=V05A_TARGET,
            practical=True,
            structural_kwargs=_STRUCTURAL,
            practical_kwargs=_PRACTICAL,
        )
        rows[world] = evidence

    directed = rows["directed_positive"]
    null = rows["interaction_null"]
    return V05BIdentificationSummary(
        directed_structural=(
            directed.structural.status is IdentificationStatus.IDENTIFIED
        ),
        directed_practical=(
            directed.practical is not None and not directed.practical.weak
        ),
        null_structural=(
            null.structural.status is IdentificationStatus.IDENTIFIED
        ),
        null_practical=(
            null.practical is not None and not null.practical.weak
        ),
        directed_target_sd=float(directed.practical.target_sd_proxy),
        null_target_sd=float(null.practical.target_sd_proxy),
    )


def _check(name, passed, observed, criterion):
    return V05BGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05b_gate(summary: V05BIdentificationSummary) -> V05BDecision:
    checks = (
        _check("directed_structural", summary.directed_structural,
               summary.directed_structural, "is True"),
        _check("directed_practical", summary.directed_practical,
               summary.directed_target_sd, "target SD <= 0.25"),
        _check("null_structural", summary.null_structural,
               summary.null_structural, "is True"),
        _check("null_practical", summary.null_practical,
               summary.null_target_sd, "target SD <= 0.25"),
    )
    return V05BDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
