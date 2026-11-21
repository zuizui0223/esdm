"""Response-blind input-support audit for process-specific geographic transfer.

This is a conservative eligibility diagnostic, *not* a test of predictive skill,
mechanistic identification, calibrated prediction, or biological validity.
The API deliberately does not accept observations or held-out model scores.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Collection, Mapping


@dataclass(frozen=True, slots=True)
class ProcessTransferSupport:
    """Input eligibility and auditable reasons, with no biological response."""

    status: str
    reasons: tuple[str, ...]
    covariates_outside_training: tuple[str, ...]
    covariates_without_target_bounds: tuple[str, ...]
    previously_unseen_source_domains: tuple[str, ...]
    independent_observation_calibration: bool

    @property
    def input_support_qualified(self) -> bool:
        """Passing this conservative screen is necessary, never sufficient."""
        return self.status == "INPUT_SUPPORT_ONLY"


def _clean_bounds(name: str, bounds: Collection[float]) -> tuple[float, float]:
    try:
        values = tuple(bounds)
    except TypeError as exc:
        raise ValueError(f"{name}: bounds must be a length-2 sequence") from exc
    if len(values) != 2:
        raise ValueError(f"{name}: bounds must contain exactly two numbers")
    if any(isinstance(value, bool) for value in values):
        raise ValueError(f"{name}: bounds cannot be booleans")
    try:
        lo, hi = (float(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: bounds must be numeric") from exc
    if not (math.isfinite(lo) and math.isfinite(hi) and lo <= hi):
        raise ValueError(f"{name}: bounds must be finite and ordered")
    return lo, hi


def _clean_domains(name: str, values: Collection[str]) -> set[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name}: expected a collection, not a string")
    try:
        result = set(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: invalid source-domain collection") from exc
    if not result or any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name}: source domains must be nonempty strings")
    return result


def audit_process_transfer_support(
    *,
    training_covariate_bounds: Mapping[str, Collection[float]],
    target_covariate_bounds: Mapping[str, Collection[float]],
    training_observation_domains: Collection[str],
    target_observation_domains: Collection[str],
    independently_calibrated_observation: bool,
) -> ProcessTransferSupport:
    """Report lack of covariate support, source overlap, and detector calibration.

    Closed min/max bounds are a *screen*, not proof of multivariate support.
    Model features must be fixed before inspecting target responses. No automatic
    knockout selection, refitting, or threshold optimization is performed.
    """
    if not training_covariate_bounds:
        raise ValueError("training_covariate_bounds must not be empty")
    if not isinstance(independently_calibrated_observation, bool):
        raise ValueError("independently_calibrated_observation must be explicitly boolean")
    if not isinstance(target_covariate_bounds, Mapping):
        raise ValueError("target_covariate_bounds must be a mapping")
    training = {}
    for name, bounds in training_covariate_bounds.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("training covariate names must be nonempty strings")
        training[name] = _clean_bounds(name, bounds)
    if any(not isinstance(name, str) or not name.strip() for name in target_covariate_bounds):
        raise ValueError("target covariate names must be nonempty strings")
    targets = {name: _clean_bounds(name, bounds) for name, bounds in target_covariate_bounds.items()}
    training_sources = _clean_domains("training_observation_domains", training_observation_domains)
    target_sources = _clean_domains("target_observation_domains", target_observation_domains)

    missing = tuple(sorted(set(training) - set(targets)))
    outside = tuple(sorted(
        name for name in training.keys() & targets.keys()
        if targets[name][0] < training[name][0] or targets[name][1] > training[name][1]
    ))
    new_sources = tuple(sorted(target_sources - training_sources))

    reasons: list[str] = []
    if missing:
        reasons.append("TARGET_COVARIATE_SUPPORT_UNKNOWN")
    if outside:
        reasons.append("TARGET_COVARIATE_EXTRAPOLATION")
    if new_sources:
        reasons.append("UNSEEN_OBSERVATION_SOURCE_DOMAIN")
    if not independently_calibrated_observation:
        reasons.append("INDEPENDENT_OBSERVATION_CALIBRATION_NOT_SUPPLIED")
    status = ("INPUT_SUPPORT_ONLY" if not reasons else
              "NOT_EVALUABLE" if missing else "TRANSFER_INPUT_NOT_QUALIFIED")
    return ProcessTransferSupport(
        status=status,
        reasons=tuple(reasons),
        covariates_outside_training=outside,
        covariates_without_target_bounds=missing,
        previously_unseen_source_domains=new_sources,
        independent_observation_calibration=independently_calibrated_observation,
    )
