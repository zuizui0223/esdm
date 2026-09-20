"""Mechanical evaluator for the frozen v0.4 state/activity promotion gate."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import IdentificationEvidence, diagnose_identification
from .v04_state_activity import (
    build_v04_state_activity_fixture,
    build_v04_unknown_detection_fixture,
    v04_identification_anchors,
    v04_unknown_detection_anchors,
)


V04_IDENTIFICATION_TARGETS = (
    "sp.activity.activity_beta_precip",
    "sp.activity.activity_beta_eastness",
    "sp.state.beta_foraging_precip",
    "sp.state.beta_foraging_eastness",
)
V04_UNKNOWN_DETECTION_TARGETS = (
    "sp.activity.activity_intercept",
    "stream.annotated.detection_intercept",
)


@dataclass(frozen=True, slots=True)
class V04IdentificationProfileResult:
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    positive_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    sparse_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    unknown_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]


@dataclass(frozen=True, slots=True)
class V04SemiSyntheticSummary:
    replicates: int
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    extrapolation_integrity: bool
    activity_beta_precip_mean_bias: float
    activity_beta_eastness_mean_bias: float
    state_beta_precip_mean_bias: float
    state_beta_eastness_mean_bias: float
    activity_beta_precip_coverage: float
    activity_beta_eastness_coverage: float
    state_beta_precip_coverage: float
    state_beta_eastness_coverage: float
    activity_positive_gain_rate: float
    mean_activity_gain: float
    state_positive_gain_rate: float
    mean_state_gain: float
    total_divergences: int
    fit_count: int


@dataclass(frozen=True, slots=True)
class V04GateConfig:
    replicates: int = 16
    fit_count: int = 48
    max_abs_bias: float = 0.15
    min_coverage: float = 0.75
    min_positive_gain_rate: float = 0.75
    min_mean_heldout_gain: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V04GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04GateDecision:
    passed: bool
    checks: tuple[V04GateCheck, ...]


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


def _known_profile_anchor_evidence(fixture):
    model, covariates = _training_model(fixture)
    structural_kwargs = {
        "method": "jax",
        "rtol": 1e-8,
        "atol": 1e-10,
    }
    practical_kwargs = {
        "rtol": 1e-8,
        "atol": 1e-10,
        "relative_singular_value_threshold": 1e-3,
        "condition_number_threshold": 1e3,
        "target_sd_threshold": 0.25,
        "fisher_ridge": 1e-10,
    }
    output = []
    for theta, theta_obs in v04_identification_anchors(fixture):
        rows = []
        for target in V04_IDENTIFICATION_TARGETS:
            rows.append(
                diagnose_identification(
                    model,
                    covariates,
                    theta=theta,
                    theta_obs=theta_obs,
                    target=target,
                    practical=True,
                    structural_kwargs=structural_kwargs,
                    practical_kwargs=practical_kwargs,
                )
            )
        output.append(tuple(rows))
    return tuple(output)


def _unknown_profile_anchor_evidence(fixture):
    model, covariates = _training_model(fixture)
    output = []
    for theta, theta_obs in v04_unknown_detection_anchors(fixture):
        rows = []
        for target in V04_UNKNOWN_DETECTION_TARGETS:
            rows.append(
                diagnose_identification(
                    model,
                    covariates,
                    theta=theta,
                    theta_obs=theta_obs,
                    target=target,
                    practical=False,
                    structural_kwargs={
                        "method": "jax",
                        "rtol": 1e-8,
                        "atol": 1e-10,
                    },
                )
            )
        output.append(tuple(rows))
    return tuple(output)


def evaluate_v04_identification_profiles(
    source_csv_text: str,
) -> V04IdentificationProfileResult:
    """Evaluate all frozen pre-MCMC v0.4 identification controls."""

    positive = build_v04_state_activity_fixture(
        source_csv_text,
        profile="positive",
    )
    sparse = build_v04_state_activity_fixture(
        source_csv_text,
        profile="sparse",
    )
    unknown = build_v04_unknown_detection_fixture(source_csv_text)

    positive_rows = _known_profile_anchor_evidence(positive)
    sparse_rows = _known_profile_anchor_evidence(sparse)
    unknown_rows = _unknown_profile_anchor_evidence(unknown)

    positive_structural = all(
        evidence.structural.status is IdentificationStatus.IDENTIFIED
        for anchor in positive_rows
        for evidence in anchor
    )
    positive_practical = all(
        evidence.practical is not None and not evidence.practical.weak
        for anchor in positive_rows
        for evidence in anchor
    )
    sparse_structural = all(
        evidence.structural.status is IdentificationStatus.IDENTIFIED
        for anchor in sparse_rows
        for evidence in anchor
    )
    sparse_refused = all(
        any(
            evidence.practical is not None and evidence.practical.weak
            for evidence in anchor
        )
        for anchor in sparse_rows
    )
    unknown_refused = all(
        evidence.structural.status is IdentificationStatus.NOT_IDENTIFIED
        for anchor in unknown_rows
        for evidence in anchor
    )
    return V04IdentificationProfileResult(
        positive_structural_pass=positive_structural,
        positive_practical_pass=positive_practical,
        sparse_structural_pass=sparse_structural,
        sparse_practical_refused=sparse_refused,
        unknown_detection_refused=unknown_refused,
        positive_anchor_evidence=positive_rows,
        sparse_anchor_evidence=sparse_rows,
        unknown_anchor_evidence=unknown_rows,
    )


def _check(name, passed, observed, criterion) -> V04GateCheck:
    return V04GateCheck(
        name=str(name),
        passed=bool(passed),
        observed=observed,
        criterion=str(criterion),
    )


def evaluate_v04_gate(
    summary: V04SemiSyntheticSummary,
    *,
    config: V04GateConfig = V04GateConfig(),
) -> V04GateDecision:
    """Apply the frozen v0.4 conjunction without making a scientific claim."""

    checks = [
        _check(
            "replicates",
            summary.replicates == config.replicates,
            summary.replicates,
            f"== {config.replicates}",
        ),
        _check(
            "fit_count",
            summary.fit_count == config.fit_count,
            summary.fit_count,
            f"== {config.fit_count}",
        ),
    ]
    for name in (
        "positive_structural_pass",
        "positive_practical_pass",
        "sparse_structural_pass",
        "sparse_practical_refused",
        "unknown_detection_refused",
        "extrapolation_integrity",
    ):
        value = bool(getattr(summary, name))
        checks.append(_check(name, value, value, "is True"))

    for prefix in (
        "activity_beta_precip",
        "activity_beta_eastness",
        "state_beta_precip",
        "state_beta_eastness",
    ):
        bias = float(getattr(summary, f"{prefix}_mean_bias"))
        coverage = float(getattr(summary, f"{prefix}_coverage"))
        checks.append(
            _check(
                f"{prefix}_bias",
                abs(bias) <= config.max_abs_bias,
                bias,
                f"abs(value) <= {config.max_abs_bias}",
            )
        )
        checks.append(
            _check(
                f"{prefix}_coverage",
                coverage >= config.min_coverage,
                coverage,
                f">= {config.min_coverage}",
            )
        )

    checks.extend(
        (
            _check(
                "activity_positive_gain_rate",
                summary.activity_positive_gain_rate
                >= config.min_positive_gain_rate,
                summary.activity_positive_gain_rate,
                f">= {config.min_positive_gain_rate}",
            ),
            _check(
                "activity_mean_gain",
                summary.mean_activity_gain
                >= config.min_mean_heldout_gain,
                summary.mean_activity_gain,
                f">= {config.min_mean_heldout_gain}",
            ),
            _check(
                "state_positive_gain_rate",
                summary.state_positive_gain_rate
                >= config.min_positive_gain_rate,
                summary.state_positive_gain_rate,
                f">= {config.min_positive_gain_rate}",
            ),
            _check(
                "state_mean_gain",
                summary.mean_state_gain
                >= config.min_mean_heldout_gain,
                summary.mean_state_gain,
                f">= {config.min_mean_heldout_gain}",
            ),
        )
    )

    mean_divergences = (
        float("inf")
        if summary.fit_count <= 0
        else summary.total_divergences / summary.fit_count
    )
    checks.append(
        _check(
            "mean_divergences_per_fit",
            mean_divergences <= config.max_mean_divergences_per_fit,
            mean_divergences,
            f"<= {config.max_mean_divergences_per_fit}",
        )
    )
    result = tuple(checks)
    return V04GateDecision(
        passed=all(check.passed for check in result),
        checks=result,
    )
