"""Practical identifiability diagnostics layered on exact structural Jacobians."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .contraction import IdentificationStatus
from .design_rank import (
    _status_from_diagnostic,
    design_jacobian_diagnostic,
)


@dataclass(frozen=True, slots=True)
class PracticalIdentificationDiagnostic:
    target: str
    structural_status: IdentificationStatus
    weak: bool
    relative_min_singular_value: float
    condition_number: float
    target_sd_proxy: float
    relative_singular_value_threshold: float
    condition_number_threshold: float
    target_sd_threshold: float | None
    reasons: tuple[str, ...] = ()


def diagnose_practical_identification(
    model,
    covariates,
    *,
    theta,
    theta_obs=None,
    target: str,
    rtol: float = 1e-10,
    atol: float = 1e-12,
    relative_singular_value_threshold: float = 1e-4,
    condition_number_threshold: float = 1e6,
    target_sd_threshold: float | None = None,
    fisher_ridge: float = 1e-10,
) -> PracticalIdentificationDiagnostic:
    """Diagnose weak separation without making a scientific support claim.

    The structural Jacobian is exact (JAX autodiff). Practical weakness is flagged when
    the full free-parameter system is nearly singular, excessively ill-conditioned, or
    has an expected Fisher-like target SD above an explicitly requested threshold.
    """

    relative_threshold = float(relative_singular_value_threshold)
    condition_threshold = float(condition_number_threshold)
    ridge = float(fisher_ridge)
    if not math.isfinite(relative_threshold) or relative_threshold <= 0.0:
        raise ValueError("relative_singular_value_threshold must be finite and positive")
    if not math.isfinite(condition_threshold) or condition_threshold <= 1.0:
        raise ValueError("condition_number_threshold must be finite and greater than one")
    if not math.isfinite(ridge) or ridge <= 0.0:
        raise ValueError("fisher_ridge must be finite and positive")
    sd_threshold = None if target_sd_threshold is None else float(target_sd_threshold)
    if sd_threshold is not None and (not math.isfinite(sd_threshold) or sd_threshold <= 0.0):
        raise ValueError("target_sd_threshold must be finite and positive when provided")

    diagnostic = design_jacobian_diagnostic(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target=target,
        rtol=rtol,
        atol=atol,
    )
    structural_status = _status_from_diagnostic(diagnostic)
    singular = diagnostic.singular_values
    parameter_count = len(diagnostic.site_names)
    if not singular or diagnostic.full_rank < parameter_count:
        relative_min = 0.0
        condition = math.inf
    else:
        largest = singular[0]
        smallest = singular[-1]
        relative_min = 0.0 if largest <= 0.0 else smallest / largest
        condition = math.inf if smallest <= 0.0 else largest / smallest

    import jax.numpy as jnp

    jacobian = jnp.asarray(diagnostic.jacobian)
    expected = jnp.asarray(diagnostic.expected_rates)
    fisher = jacobian.T @ (expected[:, None] * jacobian)
    diagonal = jnp.diag(fisher)
    scale = max(1.0, float(jnp.max(diagonal))) if int(diagonal.shape[0]) else 1.0
    regularized = fisher + ridge * scale * jnp.eye(parameter_count)
    covariance_proxy = jnp.linalg.inv(regularized)
    variance = max(0.0, float(covariance_proxy[diagnostic.target_index, diagnostic.target_index]))
    target_sd_proxy = math.sqrt(variance)

    reasons: list[str] = []
    if structural_status is not IdentificationStatus.IDENTIFIED:
        reasons.append(f"structural_status={structural_status.value}")
    if relative_min < relative_threshold:
        reasons.append(
            f"relative_min_singular_value={relative_min:.12g}<"
            f"{relative_threshold:.12g}"
        )
    if condition > condition_threshold:
        reasons.append(
            f"condition_number={condition:.12g}>{condition_threshold:.12g}"
        )
    if sd_threshold is not None and target_sd_proxy > sd_threshold:
        reasons.append(
            f"target_sd_proxy={target_sd_proxy:.12g}>{sd_threshold:.12g}"
        )

    return PracticalIdentificationDiagnostic(
        target=str(target),
        structural_status=structural_status,
        weak=bool(reasons),
        relative_min_singular_value=float(relative_min),
        condition_number=float(condition),
        target_sd_proxy=float(target_sd_proxy),
        relative_singular_value_threshold=relative_threshold,
        condition_number_threshold=condition_threshold,
        target_sd_threshold=sd_threshold,
        reasons=tuple(reasons),
    )
