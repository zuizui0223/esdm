"""Pure mechanical qualification conjunction for v0.4-R3a."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.domain import Grid
from esdm.identify import IdentificationStatus
from esdm.model import Model
from .evidence import IdentificationEvidence, diagnose_identification
from .v04_r2_gate import (
    R2_IDENTIFICATION_TARGETS,
    R2_UNKNOWN_DETECTION_TARGETS,
)
from .v04_r2_state_activity import (
    build_v04_r2_fixture,
    build_v04_r2_unknown_detection_fixture,
    v04_r2_identification_anchors,
    v04_r2_unknown_detection_anchors,
)
from .v04_r3a_design import build_v04_r3a_fixture


@dataclass(frozen=True, slots=True)
class V04R3AQualificationSummary:
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    annotated_context_count: int
    annotated_space_count: int
    annotated_time_count: int
    calibrated_context_count: int
    r2_prefix_preserved: bool


@dataclass(frozen=True, slots=True)
class V04R3ACheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V04R3ADecision:
    passed: bool
    checks: tuple[V04R3ACheck, ...]


def _check(name, passed, observed, criterion) -> V04R3ACheck:
    return V04R3ACheck(
        name=str(name),
        passed=bool(passed),
        observed=observed,
        criterion=str(criterion),
    )


def evaluate_v04_r3a_qualification(
    summary: V04R3AQualificationSummary,
) -> V04R3ADecision:
    """Apply the frozen ten-term R3a qualification conjunction."""

    checks = (
        _check(
            "positive_structural_pass",
            summary.positive_structural_pass,
            summary.positive_structural_pass,
            "is True",
        ),
        _check(
            "positive_practical_pass",
            summary.positive_practical_pass,
            summary.positive_practical_pass,
            "is True",
        ),
        _check(
            "sparse_structural_pass",
            summary.sparse_structural_pass,
            summary.sparse_structural_pass,
            "is True",
        ),
        _check(
            "sparse_practical_refused",
            summary.sparse_practical_refused,
            summary.sparse_practical_refused,
            "is True",
        ),
        _check(
            "unknown_detection_refused",
            summary.unknown_detection_refused,
            summary.unknown_detection_refused,
            "is True",
        ),
        _check(
            "annotated_context_count",
            summary.annotated_context_count == 432,
            summary.annotated_context_count,
            "== 432",
        ),
        _check(
            "annotated_space_count",
            summary.annotated_space_count == 36,
            summary.annotated_space_count,
            "== 36",
        ),
        _check(
            "annotated_time_count",
            summary.annotated_time_count == 12,
            summary.annotated_time_count,
            "== 12",
        ),
        _check(
            "calibrated_context_count",
            summary.calibrated_context_count == 432,
            summary.calibrated_context_count,
            "== 432",
        ),
        _check(
            "r2_prefix_preserved",
            summary.r2_prefix_preserved,
            summary.r2_prefix_preserved,
            "is True",
        ),
    )
    return V04R3ADecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )



@dataclass(frozen=True, slots=True)
class V04R3AIdentificationResult:
    positive_structural_pass: bool
    positive_practical_pass: bool
    sparse_structural_pass: bool
    sparse_practical_refused: bool
    unknown_detection_refused: bool
    positive_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    sparse_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]
    unknown_anchor_evidence: tuple[tuple[IdentificationEvidence, ...], ...]


_STRUCTURAL_OPTIONS = {
    "method": "jax",
    "rtol": 1e-8,
    "atol": 1e-10,
}

_PRACTICAL_OPTIONS = {
    "rtol": 1e-8,
    "atol": 1e-10,
    "relative_singular_value_threshold": 1e-3,
    "condition_number_threshold": 1e3,
    "target_sd_threshold": 0.25,
    "fisher_ridge": 1e-10,
}


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
                    structural_kwargs=_STRUCTURAL_OPTIONS,
                    practical_kwargs=_PRACTICAL_OPTIONS,
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
                    structural_kwargs=_STRUCTURAL_OPTIONS,
                )
            )
        anchors.append(tuple(rows))
    return tuple(anchors)


def evaluate_v04_r3a_identification(
    source_csv_text: str,
) -> V04R3AIdentificationResult:
    """Evaluate the frozen R3a positive design and unchanged R2 refusal controls."""

    positive = build_v04_r3a_fixture(source_csv_text)
    sparse = build_v04_r2_fixture(
        source_csv_text,
        profile="sparse",
    )
    unknown = build_v04_r2_unknown_detection_fixture(source_csv_text)

    positive_rows = _known_profile_evidence(positive)
    sparse_rows = _known_profile_evidence(sparse)
    unknown_rows = _unknown_profile_evidence(unknown)

    return V04R3AIdentificationResult(
        positive_structural_pass=all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for anchor in positive_rows
            for row in anchor
        ),
        positive_practical_pass=all(
            row.practical is not None and not row.practical.weak
            for anchor in positive_rows
            for row in anchor
        ),
        sparse_structural_pass=all(
            row.structural.status is IdentificationStatus.IDENTIFIED
            for anchor in sparse_rows
            for row in anchor
        ),
        sparse_practical_refused=all(
            any(
                row.practical is not None and row.practical.weak
                for row in anchor
            )
            for anchor in sparse_rows
        ),
        unknown_detection_refused=all(
            row.structural.status is IdentificationStatus.NOT_IDENTIFIED
            for anchor in unknown_rows
            for row in anchor
        ),
        positive_anchor_evidence=positive_rows,
        sparse_anchor_evidence=sparse_rows,
        unknown_anchor_evidence=unknown_rows,
    )


def qualification_summary(
    source_csv_text: str,
    identification: V04R3AIdentificationResult,
) -> V04R3AQualificationSummary:
    """Summarize only frozen design counts plus identification/refusal booleans."""

    fixture = build_v04_r3a_fixture(source_csv_text)
    annotated_space_count = len(fixture.annotated_spaces)
    annotated_time_count = len(fixture.annotated_times)
    calibrated_time_count = (
        len(fixture.model.domain.doy)
        * len(fixture.model.domain.hour)
    )

    return V04R3AQualificationSummary(
        positive_structural_pass=identification.positive_structural_pass,
        positive_practical_pass=identification.positive_practical_pass,
        sparse_structural_pass=identification.sparse_structural_pass,
        sparse_practical_refused=identification.sparse_practical_refused,
        unknown_detection_refused=identification.unknown_detection_refused,
        annotated_context_count=(
            annotated_space_count * annotated_time_count
        ),
        annotated_space_count=annotated_space_count,
        annotated_time_count=annotated_time_count,
        calibrated_context_count=(
            len(fixture.calibrated_spaces) * calibrated_time_count
        ),
        r2_prefix_preserved=(
            fixture.annotated_spaces[:18]
            == fixture.calibrated_spaces
        ),
    )
