"""Mechanical evaluator for the frozen v0.3.2 Gate F-prime criteria."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import IdentificationEvidence, diagnose_identification
from .v032_semisynthetic import (
    build_v032_semisynthetic_fixture,
    v032_identification_anchors,
)


@dataclass(frozen=True, slots=True)
class V032IdentificationAnchorEvidence:
    beta_precip: IdentificationEvidence
    gamma_precip: IdentificationEvidence


@dataclass(frozen=True, slots=True)
class V032IdentificationProfileResult:
    positive_structural_pass: bool
    positive_practical_pass: bool
    negative_structural_pass: bool
    negative_practical_refused: bool
    positive_anchor_evidence: tuple[V032IdentificationAnchorEvidence, ...]
    negative_anchor_evidence: tuple[V032IdentificationAnchorEvidence, ...]


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticSummary:
    replicates: int
    positive_structural_pass: bool
    positive_practical_pass: bool
    negative_structural_pass: bool
    negative_practical_refused: bool
    extrapolation_integrity: bool
    beta_precip_mean_bias: float
    gamma_precip_mean_bias: float
    beta_eastness_mean_bias: float
    beta_precip_coverage: float
    gamma_precip_coverage: float
    beta_eastness_coverage: float
    positive_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int
    fit_count: int


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticGateConfig:
    replicates: int = 20
    max_abs_bias: float = 0.15
    min_coverage: float = 0.75
    min_positive_gain_rate: float = 0.80
    min_mean_heldout_gain: float = 0.01
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticGateDecision:
    passed: bool
    checks: tuple[V032SemiSyntheticGateCheck, ...]


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
    covariates = {key: dict(fixture.covariates[key]) for key in grid.keys}
    return model, covariates


def _profile_anchor_evidence(fixture):
    model, covariates = _training_model(fixture)
    rows = []
    practical_kwargs = {
        "rtol": 1e-8,
        "atol": 1e-10,
        "relative_singular_value_threshold": 1e-3,
        "condition_number_threshold": 1e3,
        "target_sd_threshold": 0.20,
        "fisher_ridge": 1e-10,
    }
    structural_kwargs = {"method": "jax", "rtol": 1e-8, "atol": 1e-10}
    for theta, theta_obs in v032_identification_anchors(fixture):
        beta = diagnose_identification(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target="sp.suitability.beta_precip",
            structural_kwargs=structural_kwargs,
            practical_kwargs=practical_kwargs,
        )
        gamma = diagnose_identification(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target="stream.opportunistic.gamma_precip",
            structural_kwargs=structural_kwargs,
            practical_kwargs=practical_kwargs,
        )
        rows.append(V032IdentificationAnchorEvidence(beta_precip=beta, gamma_precip=gamma))
    return tuple(rows)


def evaluate_v032_identification_profiles(source_csv_text: str) -> V032IdentificationProfileResult:
    """Evaluate the frozen positive and negative design controls before outcomes."""

    positive = build_v032_semisynthetic_fixture(source_csv_text, profile="positive")
    negative = build_v032_semisynthetic_fixture(source_csv_text, profile="negative")
    positive_rows = _profile_anchor_evidence(positive)
    negative_rows = _profile_anchor_evidence(negative)

    positive_structural = all(
        row.beta_precip.structural.status is IdentificationStatus.IDENTIFIED
        and row.gamma_precip.structural.status is IdentificationStatus.IDENTIFIED
        for row in positive_rows
    )
    positive_practical = all(
        row.beta_precip.practical is not None
        and row.gamma_precip.practical is not None
        and not row.beta_precip.practical.weak
        and not row.gamma_precip.practical.weak
        for row in positive_rows
    )
    negative_structural = all(
        row.beta_precip.structural.status is IdentificationStatus.IDENTIFIED
        and row.gamma_precip.structural.status is IdentificationStatus.IDENTIFIED
        for row in negative_rows
    )
    negative_refused = all(
        row.beta_precip.practical is not None
        and row.gamma_precip.practical is not None
        and (row.beta_precip.practical.weak or row.gamma_precip.practical.weak)
        for row in negative_rows
    )
    return V032IdentificationProfileResult(
        positive_structural_pass=positive_structural,
        positive_practical_pass=positive_practical,
        negative_structural_pass=negative_structural,
        negative_practical_refused=negative_refused,
        positive_anchor_evidence=positive_rows,
        negative_anchor_evidence=negative_rows,
    )


def evaluate_v032_semisynthetic_gate(
    summary: V032SemiSyntheticSummary,
    *,
    config: V032SemiSyntheticGateConfig | None = None,
) -> V032SemiSyntheticGateDecision:
    """Evaluate all frozen F-prime terms as a non-compensatory conjunction."""

    cfg = V032SemiSyntheticGateConfig() if config is None else config
    mean_divergences = (
        float(summary.total_divergences) / float(summary.fit_count)
        if summary.fit_count > 0
        else float("inf")
    )

    checks = (
        V032SemiSyntheticGateCheck("replicates", summary.replicates == cfg.replicates, summary.replicates, f"replicates == {cfg.replicates}"),
        V032SemiSyntheticGateCheck("positive_structural_pass", bool(summary.positive_structural_pass), summary.positive_structural_pass, "positive profile structural identification passes at all frozen anchors"),
        V032SemiSyntheticGateCheck("positive_practical_pass", bool(summary.positive_practical_pass), summary.positive_practical_pass, "positive profile is practically identified at all frozen anchors"),
        V032SemiSyntheticGateCheck("negative_structural_pass", bool(summary.negative_structural_pass), summary.negative_structural_pass, "negative profile remains structurally identified"),
        V032SemiSyntheticGateCheck("negative_practical_refused", bool(summary.negative_practical_refused), summary.negative_practical_refused, "negative profile is refused as practically weak"),
        V032SemiSyntheticGateCheck("extrapolation_integrity", bool(summary.extrapolation_integrity), summary.extrapolation_integrity, "min heldout eastness > max training eastness"),
        V032SemiSyntheticGateCheck("beta_precip_bias", abs(float(summary.beta_precip_mean_bias)) <= cfg.max_abs_bias, summary.beta_precip_mean_bias, f"abs(mean bias) <= {cfg.max_abs_bias}"),
        V032SemiSyntheticGateCheck("gamma_precip_bias", abs(float(summary.gamma_precip_mean_bias)) <= cfg.max_abs_bias, summary.gamma_precip_mean_bias, f"abs(mean bias) <= {cfg.max_abs_bias}"),
        V032SemiSyntheticGateCheck("beta_eastness_bias", abs(float(summary.beta_eastness_mean_bias)) <= cfg.max_abs_bias, summary.beta_eastness_mean_bias, f"abs(mean bias) <= {cfg.max_abs_bias}"),
        V032SemiSyntheticGateCheck("beta_precip_coverage", float(summary.beta_precip_coverage) >= cfg.min_coverage, summary.beta_precip_coverage, f"coverage >= {cfg.min_coverage}"),
        V032SemiSyntheticGateCheck("gamma_precip_coverage", float(summary.gamma_precip_coverage) >= cfg.min_coverage, summary.gamma_precip_coverage, f"coverage >= {cfg.min_coverage}"),
        V032SemiSyntheticGateCheck("beta_eastness_coverage", float(summary.beta_eastness_coverage) >= cfg.min_coverage, summary.beta_eastness_coverage, f"coverage >= {cfg.min_coverage}"),
        V032SemiSyntheticGateCheck("heldout_positive_gain_rate", float(summary.positive_gain_rate) >= cfg.min_positive_gain_rate, summary.positive_gain_rate, f"positive gain rate >= {cfg.min_positive_gain_rate}"),
        V032SemiSyntheticGateCheck("heldout_mean_gain", float(summary.mean_heldout_gain) >= cfg.min_mean_heldout_gain, summary.mean_heldout_gain, f"mean gain >= {cfg.min_mean_heldout_gain}"),
        V032SemiSyntheticGateCheck("mean_divergences_per_fit", mean_divergences <= cfg.max_mean_divergences_per_fit, mean_divergences, f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}"),
    )
    return V032SemiSyntheticGateDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
