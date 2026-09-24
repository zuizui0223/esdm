"""Identification and replicated outcome gate for v0.5a."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import IdentificationStatus
from .evidence import diagnose_identification
from .v05a_directed import V05A_TARGET, build_v05a_fixture
from .v05a_run import V05ASummary, _subset_model


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
class V05AIdentificationSummary:
    directed_structural: bool
    directed_practical: bool
    null_structural: bool
    null_practical: bool
    directed_target_sd: float
    null_target_sd: float


@dataclass(frozen=True, slots=True)
class V05AGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V05ADecision:
    passed: bool
    checks: tuple[V05AGateCheck, ...]


def evaluate_v05a_identification(source_csv_text: str) -> V05AIdentificationSummary:
    rows = {}
    for world in ("directed_positive", "interaction_null"):
        fixture = build_v05a_fixture(source_csv_text, world=world)
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
    return V05AIdentificationSummary(
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
    return V05AGateCheck(str(name), bool(passed), observed, str(criterion))


def evaluate_v05a_identification_gate(
    identification: V05AIdentificationSummary,
) -> V05ADecision:
    checks = (
        _check("directed_structural", identification.directed_structural,
               identification.directed_structural, "is True"),
        _check("directed_practical", identification.directed_practical,
               identification.directed_target_sd, "target SD <= 0.25"),
        _check("null_structural", identification.null_structural,
               identification.null_structural, "is True"),
        _check("null_practical", identification.null_practical,
               identification.null_target_sd, "target SD <= 0.25"),
    )
    return V05ADecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def evaluate_v05a_gate(
    identification: V05AIdentificationSummary,
    outcome: V05ASummary,
) -> V05ADecision:
    directed = outcome.worlds["directed_positive"]
    null = outcome.worlds["interaction_null"]
    mean_divergences = (
        float("inf")
        if outcome.fit_count <= 0
        else outcome.total_divergences / outcome.fit_count
    )

    checks = (
        _check("directed_structural", identification.directed_structural,
               identification.directed_structural, "is True"),
        _check("directed_practical", identification.directed_practical,
               identification.directed_target_sd, "target SD <= 0.25"),
        _check("null_structural", identification.null_structural,
               identification.null_structural, "is True"),
        _check("null_practical", identification.null_practical,
               identification.null_target_sd, "target SD <= 0.25"),
        _check("directed_replicates", directed.replicates == 16,
               directed.replicates, "== 16"),
        _check("null_replicates", null.replicates == 16,
               null.replicates, "== 16"),
        _check("fit_count", outcome.fit_count == 64,
               outcome.fit_count, "== 64"),
        _check("extrapolation_integrity", outcome.extrapolation_integrity,
               outcome.extrapolation_integrity, "is True"),
        _check("directed_abs_bias", abs(directed.mean_bias) <= 0.15,
               directed.mean_bias, "abs(mean bias) <= 0.15"),
        _check("directed_coverage", directed.truth_coverage >= 0.75,
               directed.truth_coverage, ">= 0.75"),
        _check("directed_nonzero", directed.nonzero_rate >= 0.75,
               directed.nonzero_rate, ">= 0.75"),
        _check("directed_positive_gain", directed.positive_gain_rate >= 0.75,
               directed.positive_gain_rate, ">= 0.75"),
        _check("directed_mean_gain", directed.mean_heldout_gain >= 0.005,
               directed.mean_heldout_gain, ">= 0.005"),
        _check("null_abs_mean_beta", abs(null.mean_beta) <= 0.15,
               null.mean_beta, "abs(mean beta) <= 0.15"),
        _check("null_coverage", null.truth_coverage >= 0.75,
               null.truth_coverage, ">= 0.75"),
        _check("null_nonzero", null.nonzero_rate <= 0.25,
               null.nonzero_rate, "<= 0.25"),
        _check("null_material_gain", null.material_gain_rate <= 0.25,
               null.material_gain_rate, "<= 0.25"),
        _check("null_mean_gain", null.mean_heldout_gain <= 0.005,
               null.mean_heldout_gain, "<= 0.005"),
        _check("mean_divergences_per_fit", mean_divergences <= 0.10,
               mean_divergences, "<= 0.10"),
    )
    return V05ADecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
