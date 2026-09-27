"""Prior-to-posterior contraction diagnostics.

Identification is deliberately kept separate from scientific support. Posterior
contraction can show that a parameter is informed under the declared model, but it
cannot by itself make an ecological claim Supported.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import statistics


@dataclass(frozen=True, slots=True)
class ContractionDiagnostic:
    prior_sd: float
    posterior_sd: float
    contraction_fraction: float
    n_draws: int


class IdentificationStatus(str, Enum):
    DESIGN_UNINFORMED = "DesignUninformed"
    NOT_IDENTIFIED = "NotIdentified"
    IDENTIFIED = "Identified"


@dataclass(frozen=True, slots=True)
class IdentificationResult:
    status: IdentificationStatus
    target: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        target = str(self.target).strip()
        if not target:
            raise ValueError("identification target must be non-empty")
        if not isinstance(self.status, IdentificationStatus):
            raise TypeError("status must be an IdentificationStatus")
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "evidence", tuple(str(value) for value in self.evidence))


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
) -> IdentificationResult:
    """Classify parameter identification without making a support claim."""

    threshold = float(minimum_contraction)
    if not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0:
        raise ValueError("minimum_contraction must be in [0, 1]")
    status = (
        IdentificationStatus.IDENTIFIED
        if diagnostic.contraction_fraction >= threshold
        else IdentificationStatus.NOT_IDENTIFIED
    )
    return IdentificationResult(
        status=status,
        target=target,
        evidence=(
            f"prior_sd={diagnostic.prior_sd}",
            f"posterior_sd={diagnostic.posterior_sd}",
            f"contraction={diagnostic.contraction_fraction}",
        ),
    )
