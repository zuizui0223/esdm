"""Held-out community transfer scoring."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping, Sequence
from types import MappingProxyType

from .ceiling import PointTransferCeiling, point_transfer_ceiling


@dataclass(frozen=True, slots=True)
class HeldoutCommunityPrediction:
    community_id: str
    outcomes: tuple[int, ...]
    baseline_probabilities: tuple[float, ...]
    enriched_probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.community_id, str) or not self.community_id.strip():
            raise ValueError("community_id must be a non-empty string")
        outcomes = tuple(self.outcomes)
        baseline = tuple(float(value) for value in self.baseline_probabilities)
        enriched = tuple(float(value) for value in self.enriched_probabilities)
        if not outcomes:
            raise ValueError("each held-out community must contain at least one outcome")
        if not (len(outcomes) == len(baseline) == len(enriched)):
            raise ValueError("outcomes and probability vectors must have equal length")
        if any(value not in (0, 1, False, True) for value in outcomes):
            raise ValueError("outcomes must be binary")
        if any(not math.isfinite(p) or not 0.0 <= p <= 1.0 for p in baseline + enriched):
            raise ValueError("probabilities must be finite values in [0, 1]")
        object.__setattr__(self, "outcomes", tuple(int(value) for value in outcomes))
        object.__setattr__(self, "baseline_probabilities", baseline)
        object.__setattr__(self, "enriched_probabilities", enriched)


@dataclass(frozen=True, slots=True)
class CommunityGainResult:
    per_community: Mapping[str, float]
    macro_gain: float
    n_communities: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "per_community", MappingProxyType(dict(self.per_community)))


def _mean_bernoulli_log_score(
    outcomes: Sequence[int], probabilities: Sequence[float], *, clip: float = 1e-15
) -> float:
    scores: list[float] = []
    for outcome, probability in zip(outcomes, probabilities, strict=True):
        p = min(max(float(probability), clip), 1.0 - clip)
        scores.append(math.log(p if outcome else 1.0 - p))
    return math.fsum(scores) / len(scores)


def community_log_score_gain(
    predictions: Sequence[HeldoutCommunityPrediction],
) -> CommunityGainResult:
    """Macro-average enriched-minus-baseline log-score gain by community."""

    if not predictions:
        raise ValueError("at least one held-out community is required")
    seen: set[str] = set()
    gains: dict[str, float] = {}
    for prediction in predictions:
        if prediction.community_id in seen:
            raise ValueError("community_id values must be unique")
        seen.add(prediction.community_id)
        baseline = _mean_bernoulli_log_score(
            prediction.outcomes, prediction.baseline_probabilities
        )
        enriched = _mean_bernoulli_log_score(
            prediction.outcomes, prediction.enriched_probabilities
        )
        gains[prediction.community_id] = enriched - baseline

    macro_gain = math.fsum(gains.values()) / len(gains)
    return CommunityGainResult(
        per_community=gains,
        macro_gain=macro_gain,
        n_communities=len(gains),
    )


def community_information_ceiling(
    *,
    base_level: str,
    ordered_steps: Sequence[tuple[str, str]],
    gains_by_step: Mapping[str, CommunityGainResult],
    tolerance: float = 0.0,
) -> PointTransferCeiling:
    """Non-skippable point ceiling using each step's macro-community gain."""

    point_gains = {
        step: (result.macro_gain,) for step, result in gains_by_step.items()
    }
    return point_transfer_ceiling(
        base_level=base_level,
        ordered_steps=ordered_steps,
        gains_by_step=point_gains,
        tolerance=tolerance,
    )
