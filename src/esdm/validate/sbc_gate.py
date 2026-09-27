"""Frozen v0.3 simulation-based calibration gate."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.identify import SBCRankHistogram, sbc_rank_histogram
from .known_truth import PromotionGateCheck


@dataclass(frozen=True, slots=True)
class V03SBCGateConfig:
    target: str = "sp.suitability.beta_x"
    replicates: int = 100
    bins: int = 10
    max_total_variation: float = 0.20
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V03SBCGateDecision:
    target: str
    passed: bool
    histogram: SBCRankHistogram
    mean_divergences: float
    checks: tuple[PromotionGateCheck, ...]


def evaluate_v03_sbc_gate(result, *, config: V03SBCGateConfig | None = None) -> V03SBCGateDecision:
    """Evaluate the pre-outcome SBC gate without mixing it with misspecification tests."""

    cfg = V03SBCGateConfig() if config is None else config
    if cfg.target not in result.ranks:
        raise ValueError(f"SBC result missing frozen target {cfg.target!r}")
    if len(result.divergences_by_replicate) != result.replicates:
        raise ValueError("SBC divergence vector length must equal replicate count")

    histogram = sbc_rank_histogram(
        ranks=result.ranks[cfg.target],
        posterior_draw_count=result.posterior_draw_count,
        bins=cfg.bins,
        max_total_variation=cfg.max_total_variation,
    )
    mean_divergences = (
        sum(int(value) for value in result.divergences_by_replicate) / result.replicates
        if result.replicates
        else float("inf")
    )
    checks = (
        PromotionGateCheck(
            "sbc_replicates",
            result.replicates == cfg.replicates,
            result.replicates,
            f"replicates == {cfg.replicates}",
        ),
        PromotionGateCheck(
            "sbc_rank_uniformity",
            histogram.calibrated,
            histogram.total_variation,
            f"rank-histogram total variation <= {cfg.max_total_variation}",
        ),
        PromotionGateCheck(
            "sbc_divergences",
            mean_divergences <= cfg.max_mean_divergences_per_fit,
            mean_divergences,
            f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
        ),
    )
    return V03SBCGateDecision(
        target=cfg.target,
        passed=all(check.passed for check in checks),
        histogram=histogram,
        mean_divergences=mean_divergences,
        checks=checks,
    )
