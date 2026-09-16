"""Prior-to-posterior contraction diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics

from esdm.claims.types import Claim, ClaimStatus
from esdm.core import InteractionEvidenceTier


@dataclass(frozen=True, slots=True)
class ContractionDiagnostic:
    prior_sd: float
    posterior_sd: float
    contraction_fraction: float
    n_draws: int


def contraction_diagnostic(*, prior_sd: float, posterior_samples) -> ContractionDiagnostic:
    prior = float(prior_sd)
    samples = tuple(float(value) for value in posterior_samples)
    if not math.isfinite(prior) or prior <= 0.0:
        raise ValueError("prior_sd must be finite and positive")
    if len(samples) < 2 or any(not math.isfinite(value) for value in samples):
        raise ValueError("posterior_samples must contain at least two finite values")
    posterior = float(statistics.pstdev(samples))
    contraction = 1.0 - posterior / prior
    return ContractionDiagnostic(prior, posterior, contraction, len(samples))


def identify_from_contraction(
    diagnostic: ContractionDiagnostic,
    *,
    minimum_contraction: float,
    target: str,
) -> Claim:
    threshold = float(minimum_contraction)
    if not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0:
        raise ValueError("minimum_contraction must be in [0, 1]")
    status = (
        ClaimStatus.SUPPORTED
        if diagnostic.contraction_fraction >= threshold
        else ClaimStatus.NOT_IDENTIFIED
    )
    return Claim(
        status=status,
        tier=InteractionEvidenceTier.COAVAILABLE,
        target=target,
        evidence=(
            f"prior_sd={diagnostic.prior_sd}",
            f"posterior_sd={diagnostic.posterior_sd}",
            f"contraction={diagnostic.contraction_fraction}",
        ),
    )
