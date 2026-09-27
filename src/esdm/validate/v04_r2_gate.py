"""Mechanical evaluator for the frozen v0.4-R2 hard separation gate."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import IdentificationEvidence, diagnose_identification
from .v04_r2_state_activity import (
    build_v04_r2_fixture,
    build_v04_r2_unknown_detection_fixture,
    v04_r2_identification_anchors,
    v04_r2_unknown_detection_anchors,
)


R2_IDENTIFICATION_TARGETS = (
    "sp.suitability.beta_precip",
    "stream.opportunistic.gamma_precip",
    "stream.opportunistic.gamma_season",
    "stream.opportunistic.gamma_hour",
    "stream.opportunistic.detection_intercept",
    "sp.activity.activity_beta_precip",
    "sp.activity.activity_beta_eastness",
    "sp.activity.activity_beta_season",
    "sp.activity.activity_beta_hour",
    "sp.state.beta_foraging_precip",
    "sp.state.beta_foraging_eastness",
    "sp.state.beta_foraging_season",
    "sp.state.beta_foraging_hour",
)

R2_UNKNOWN_DETECTION_TARGETS = (
    "sp.activity.activity_intercept",
    "stream.annotated.detection_intercept",
)

R2_RECOVERY_TRUTH = MappingProxyType(
    {
        "sp.suitability.beta_precip": 0.45,
        "stream.opportunistic.gamma_precip": 0.35,
        "stream.opportunistic.gamma_season": 0.30,
        "stream.opportunistic.gamma_hour": -0.25,
        "stream.opportunistic.detection_intercept": -0.20,
        "sp.activity.activity_beta_precip": 0.50,
        "sp.activity.activity_beta_eastness": 0.35,
        "sp.activity.activity_beta_season": 0.55,
        "sp.activity.activity_beta_hour": 0.40,
        "sp.state.beta_foraging_precip": -0.45,
        "sp.state.beta_foraging_eastness": 0.40,
        "sp.state.beta_foraging_season": 0.50,
        "sp.state.beta_foraging_hour": -0.45,
    }
)


@dataclass(frozen=True, slots=True)
class V04R2IdentificationProfileResult:
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    positive_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    sparse_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    unknown_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]


@dataclass(frozen=True, slots=True)
class V04R2Summary:
    replicates: int
    fit_count: int
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    extrapolation_integrity: bool
    mean_biases: Mapping[str, float]
    coverages: Mapping[str, float]
    activity_positive_gain_rate: float
    mean_activity_gain: float
    state_positive_gain_rate: float
    mean_state_gain: float
    total_divergences: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mean_biases",
            MappingProxyType(
                {
                    str(key): float(value)
                    for key, value in self.mean_biases.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "coverages",
            MappingProxyType(
                {
                    str(key): float(value)
                    for key, value in self.coverages.items()
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class V04R2GateConfig:
    replicates: int = 16
    fit_count: int = 48
    max_abs_bias: float = 0.18
    min_coverage: float = 0.75
    min_positive_gain_rate: float = 0.75
    min_mean_heldout_gain: float = 0.005
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V04R2GateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04R2GateDecision:
    passed: bool
    checks: tuple[V04R2GateCheck, ...]


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


def _known_profile_evidence(fixture):
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
    anchors = []
    for theta, theta_obs in v04_r2_identification_anchors(fixture):
        rows = []
        for target in R2_IDENTIFICATION_TARGETS:
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
        anchors.append(tuple(rows))
    return tuple(anchors)


def _unknown_profile_evidence(fixture):
    model, covariates = _training_model(fixture)
    anchors = []
    for theta, theta_obs in v04_r2_unknown_detection_anchors(fixture):
        rows = []
        for target in R2_UNKNOWN_DETECTION_TARGETS:
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
        anchors.append(tuple(rows))
    return tuple(anchors)


def evaluate_v04_r2_identification_profiles(
    source_csv_text: str,
) -> V04R2IdentificationProfileResult:
    positive = build_v04_r2_fixture(
        source_csv_text,
        profile="positive",
    )
    sparse = build_v04_r2_fixture(
        source_csv_text,
        profile="sparse",
    )
    unknown = build_v04_r2_unknown_detection_fixture(source_csv_text)

    positive_rows = _known_profile_evidence(positive)
    sparse_rows = _known_profile_evidence(sparse)
    unknown_rows = _unknown_profile_evidence(unknown)

    positive_structural = all(
        row.structural.status is IdentificationStatus.IDENTIFIED
        for anchor in positive_rows
        for row in anchor
    )
    positive_practical = all(
        row.practical is not None and not row.practical.weak
        for anchor in positive_rows
        for row in anchor
    )
    sparse_structural = all(
        row.structural.status is IdentificationStatus.IDENTIFIED
        for anchor in sparse_rows
        for row in anchor
    )
    sparse_refused = all(
        any(
            row.practical is not None and row.practical.weak
            for row in anchor
        )
        for anchor in sparse_rows
    )
    unknown_refused = all(
        row.structural.status is IdentificationStatus.NOT_IDENTIFIED
        for anchor in unknown_rows
        for row in anchor
    )
    return V04R2IdentificationProfileResult(
        positive_structural_pass=positive_structural,
        positive_practical_pass=positive_practical,
        sparse_structural_pass=sparse_structural,
        sparse_practical_refused=sparse_refused,
        unknown_detection_refused=unknown_refused,
        positive_anchor_evidence=positive_rows,
        sparse_anchor_evidence=sparse_rows,
        unknown_anchor_evidence=unknown_rows,
    )


def _check(name, passed, observed, criterion) -> V04R2GateCheck:
    return V04R2GateCheck(
        name=str(name),
        passed=bool(passed),
        observed=observed,
        criterion=str(criterion),
    )


def _validate_recovery_maps(summary: V04R2Summary) -> None:
    expected = set(R2_RECOVERY_TRUTH)
    if set(summary.mean_biases) != expected:
        raise ValueError(
            "mean_biases recovery targets must match frozen R2 recovery targets"
        )
    if set(summary.coverages) != expected:
        raise ValueError(
            "coverages recovery targets must match frozen R2 recovery targets"
        )


def evaluate_v04_r2_gate(
    summary: V04R2Summary,
    *,
    config: V04R2GateConfig = V04R2GateConfig(),
) -> V04R2GateDecision:
    _validate_recovery_maps(summary)
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
        observed = bool(getattr(summary, name))
        checks.append(_check(name, observed, observed, "is True"))

    for target in R2_RECOVERY_TRUTH:
        bias = float(summary.mean_biases[target])
        coverage = float(summary.coverages[target])
        checks.append(
            _check(
                f"{target}.bias",
                abs(bias) <= config.max_abs_bias,
                bias,
                f"abs(value) <= {config.max_abs_bias}",
            )
        )
        checks.append(
            _check(
                f"{target}.coverage",
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
    return V04R2GateDecision(
        passed=all(check.passed for check in result),
        checks=result,
    )
