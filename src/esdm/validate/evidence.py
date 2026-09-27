"""Reusable validation evidence primitives with no claim-promotion semantics.

These objects record what a design, knockout, or held-out comparison shows. They do
not assign scientific claim status or evidence tier; promotion remains an explicit
separate policy decision.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from esdm.identify import (
    IdentificationResult,
    PracticalIdentificationDiagnostic,
    diagnose_practical_identification,
    identify_parameter_from_design,
)


@dataclass(frozen=True, slots=True)
class IdentificationEvidence:
    target: str
    structural: IdentificationResult
    practical: PracticalIdentificationDiagnostic | None = None


@dataclass(frozen=True, slots=True)
class KnockoutEvidence:
    stream_name: str
    species: str
    n_contexts: int
    full_log_score: float
    knockout_log_score: float
    gain: float


@dataclass(frozen=True, slots=True)
class TransferEvidence:
    heldout_label: str
    stream_name: str
    species: str
    n_contexts: int
    candidate_log_score: float
    reference_log_score: float
    gain: float


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    identifications: tuple[IdentificationEvidence, ...] = ()
    knockout: KnockoutEvidence | None = None
    transfer: TransferEvidence | None = None


def diagnose_identification(
    model,
    covariates,
    *,
    theta,
    theta_obs=None,
    target: str,
    practical: bool = True,
    structural_kwargs: Mapping[str, object] | None = None,
    practical_kwargs: Mapping[str, object] | None = None,
) -> IdentificationEvidence:
    """Collect structural and optional practical diagnostics as evidence only."""

    structural_options = {} if structural_kwargs is None else dict(structural_kwargs)
    structural = identify_parameter_from_design(
        model,
        covariates,
        theta=theta,
        theta_obs=theta_obs,
        target=target,
        **structural_options,
    )
    practical_result = None
    if practical:
        practical_options = {} if practical_kwargs is None else dict(practical_kwargs)
        practical_result = diagnose_practical_identification(
            model,
            covariates,
            theta=theta,
            theta_obs=theta_obs,
            target=target,
            **practical_options,
        )
    return IdentificationEvidence(
        target=str(target),
        structural=structural,
        practical=practical_result,
    )


def _logmeanexp(values) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("logmeanexp needs at least one value")
    maximum = max(rows)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in rows) / len(rows))


def _poisson_log_mass(count: int, rate: float) -> float:
    y = int(count)
    lam = float(rate)
    if y < 0 or not math.isfinite(lam) or lam < 0.0:
        raise ValueError("invalid Poisson count/rate")
    if lam == 0.0:
        return 0.0 if y == 0 else -math.inf
    return y * math.log(lam) - lam - math.lgamma(y + 1.0)


def poisson_log_predictive_density(
    model,
    samples,
    covariates,
    data,
    *,
    stream_name: str,
    species: str,
) -> float:
    """Mean context-wise posterior log predictive density for Poisson records."""

    from esdm.model.backend_numpyro import posterior_record_rates

    stream_name = str(stream_name)
    species = str(species)
    matching_streams = tuple(stream for stream in model.streams if stream.name == stream_name)
    if len(matching_streams) != 1:
        raise KeyError(f"unknown observation stream {stream_name!r}")
    stream = matching_streams[0]
    if species not in model.stream_targets(stream):
        raise KeyError(f"species {species!r} is not targeted by stream {stream_name!r}")
    if stream_name not in data or species not in data[stream_name]:
        raise KeyError(f"missing held-out data for {stream_name}:{species}")

    rate_draws = posterior_record_rates(model, samples, covariates)[(stream_name, species)]
    if not rate_draws:
        raise ValueError("posterior predictive rates must contain at least one draw")
    ordered_keys = tuple(model.domain.keys)
    if any(len(draw) != len(ordered_keys) for draw in rate_draws):
        raise ValueError("posterior rate draws do not match the model domain")
    counts_map = data[stream_name][species]
    unknown = set(counts_map) - set(ordered_keys)
    if unknown:
        raise ValueError("held-out counts contain contexts outside the model domain")
    ordered_counts = tuple(int(counts_map.get(key, 0)) for key in ordered_keys)
    if any(count < 0 for count in ordered_counts):
        raise ValueError("held-out counts must be non-negative")

    context_scores = []
    for index, count in enumerate(ordered_counts):
        context_scores.append(
            _logmeanexp(
                _poisson_log_mass(count, draw[index])
                for draw in rate_draws
            )
        )
    return math.fsum(context_scores) / len(context_scores)


def _validate_comparison_domains(candidate_model, reference_model) -> int:
    candidate_keys = tuple(candidate_model.domain.keys)
    reference_keys = tuple(reference_model.domain.keys)
    if candidate_keys != reference_keys:
        raise ValueError("predictive comparison models must use the same ordered held-out contexts")
    if not candidate_keys:
        raise ValueError("predictive comparison requires at least one held-out context")
    return len(candidate_keys)


def compare_knockout(
    full_model,
    full_samples,
    knockout_model,
    knockout_samples,
    *,
    full_covariates,
    knockout_covariates,
    data,
    stream_name: str,
    species: str,
) -> KnockoutEvidence:
    """Compare a fitted full model against its declared knockout on held-out counts."""

    n_contexts = _validate_comparison_domains(full_model, knockout_model)
    full_score = poisson_log_predictive_density(
        full_model,
        full_samples,
        full_covariates,
        data,
        stream_name=stream_name,
        species=species,
    )
    knockout_score = poisson_log_predictive_density(
        knockout_model,
        knockout_samples,
        knockout_covariates,
        data,
        stream_name=stream_name,
        species=species,
    )
    return KnockoutEvidence(
        stream_name=str(stream_name),
        species=str(species),
        n_contexts=n_contexts,
        full_log_score=full_score,
        knockout_log_score=knockout_score,
        gain=full_score - knockout_score,
    )


def evaluate_transfer(
    candidate_model,
    candidate_samples,
    reference_model,
    reference_samples,
    *,
    candidate_covariates,
    reference_covariates,
    data,
    stream_name: str,
    species: str,
    heldout_label: str,
) -> TransferEvidence:
    """Compare two fitted models on the same held-out Poisson observations."""

    label = str(heldout_label).strip()
    if not label:
        raise ValueError("heldout_label must be non-empty")
    n_contexts = _validate_comparison_domains(candidate_model, reference_model)
    candidate_score = poisson_log_predictive_density(
        candidate_model,
        candidate_samples,
        candidate_covariates,
        data,
        stream_name=stream_name,
        species=species,
    )
    reference_score = poisson_log_predictive_density(
        reference_model,
        reference_samples,
        reference_covariates,
        data,
        stream_name=stream_name,
        species=species,
    )
    return TransferEvidence(
        heldout_label=label,
        stream_name=str(stream_name),
        species=str(species),
        n_contexts=n_contexts,
        candidate_log_score=candidate_score,
        reference_log_score=reference_score,
        gain=candidate_score - reference_score,
    )
