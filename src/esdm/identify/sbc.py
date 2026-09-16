"""Lightweight simulation-based calibration rank diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class SBCRankHistogram:
    counts: tuple[int, ...]
    total_variation: float
    calibrated: bool
    posterior_draw_count: int


def sbc_rank_histogram(
    *,
    ranks,
    posterior_draw_count: int,
    bins: int,
    max_total_variation: float = 0.1,
) -> SBCRankHistogram:
    draw_count = int(posterior_draw_count)
    bins = int(bins)
    if draw_count < 1:
        raise ValueError("posterior_draw_count must be positive")
    if bins < 2 or bins > draw_count + 1:
        raise ValueError("bins must be in 2..posterior_draw_count+1")
    threshold = float(max_total_variation)
    if not math.isfinite(threshold) or threshold < 0.0 or threshold > 1.0:
        raise ValueError("max_total_variation must be in [0, 1]")
    values = tuple(int(rank) for rank in ranks)
    if not values:
        raise ValueError("ranks must be non-empty")
    if any(rank < 0 or rank > draw_count for rank in values):
        raise ValueError("SBC ranks must be in 0..posterior_draw_count")

    counts = [0] * bins
    support = draw_count + 1
    for rank in values:
        index = min(bins - 1, (rank * bins) // support)
        counts[index] += 1
    n = len(values)
    expected = 1.0 / bins
    total_variation = 0.5 * sum(abs(count / n - expected) for count in counts)
    return SBCRankHistogram(
        counts=tuple(counts),
        total_variation=total_variation,
        calibrated=bool(total_variation <= threshold),
        posterior_draw_count=draw_count,
    )
