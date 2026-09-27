"""Simulation-based calibration diagnostics.

The legacy rank-histogram helper is retained for reproducibility of the retired v0.3
benchmark. v0.3.1 uses ESS-aware rank supports and a simulation-based simultaneous
ECDF envelope across every declared free parameter.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math
import random


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
    """Legacy binned SBC diagnostic retained for retired v0.3 reproducibility."""

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


@dataclass(frozen=True, slots=True)
class ESSThinnedDraws:
    draws: tuple[object, ...]
    stride: int
    draw_count: int
    effective_sample_size: float


def ess_thin_draws(draws, *, effective_sample_size: float) -> ESSThinnedDraws:
    """Thin one posterior sequence using an ESS-derived stride.

    The function does not estimate ESS; inference backends should supply an ESS estimate
    computed from the chain structure. The retained draw count is recorded because SBC
    ranks are discrete-uniform on ``0..draw_count`` conditional on that support.
    """

    values = tuple(draws)
    if not values:
        raise ValueError("draws must be non-empty")
    ess = float(effective_sample_size)
    if not math.isfinite(ess) or ess <= 0.0:
        raise ValueError("effective_sample_size must be finite and positive")
    effective = min(float(len(values)), ess)
    stride = max(1, int(math.ceil(len(values) / effective)))
    thinned = tuple(values[::stride])
    return ESSThinnedDraws(
        draws=thinned,
        stride=stride,
        draw_count=len(thinned),
        effective_sample_size=ess,
    )


@dataclass(frozen=True, slots=True)
class SBCSimultaneousECDFResult:
    passed: bool
    alpha: float
    simulations: int
    evaluation_grid: tuple[float, ...]
    critical_max_deviation: float
    observed_max_deviation: float
    parameter_max_deviation: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameter_max_deviation",
            MappingProxyType(dict(self.parameter_max_deviation)),
        )


def _fractional_rank(rank: int, draw_count: int) -> float:
    # Midpoint transform for a discrete rank support 0..draw_count.
    return (int(rank) + 0.5) / (int(draw_count) + 1.0)


def _null_ecdf_at(z: float, draw_counts: tuple[int, ...]) -> float:
    total = 0.0
    for draw_count in draw_counts:
        support = draw_count + 1
        # Number of k in 0..draw_count with (k + 0.5) / support <= z.
        maximum_k = math.floor(z * support - 0.5)
        accepted = min(support, max(0, maximum_k + 1))
        total += accepted / support
    return total / len(draw_counts)


def _parameter_max_deviation(
    ranks: tuple[int, ...],
    draw_counts: tuple[int, ...],
    grid: tuple[float, ...],
) -> float:
    values = sorted(_fractional_rank(rank, count) for rank, count in zip(ranks, draw_counts))
    n = len(values)
    maximum = 0.0
    for z in grid:
        observed = bisect_right(values, z) / n
        expected = _null_ecdf_at(z, draw_counts)
        maximum = max(maximum, abs(observed - expected))
    return maximum


def sbc_ecdf_simultaneous_test(
    *,
    ranks: Mapping[str, tuple[int, ...] | list[int]],
    draw_counts: Mapping[str, tuple[int, ...] | list[int]],
    alpha: float = 0.05,
    simulations: int = 10_000,
    seed: int = 0,
    evaluation_points: int = 49,
) -> SBCSimultaneousECDFResult:
    """Test discrete-uniform SBC ranks with a familywise ECDF envelope.

    For every parameter, ranks are transformed using their replicate-specific finite
    support. A Monte Carlo null draws ranks from exactly those supports and records the
    maximum absolute ECDF deviation across *all parameters and all evaluation points*.
    The ``1-alpha`` quantile of that familywise maximum is the simultaneous envelope.

    This is the simulation-based simultaneous-band strategy for discrete uniformity,
    specialized to SBC and extended here to control the whole declared parameter family
    in one gate. It intentionally does not bin ranks or use a total-variation threshold.
    """

    if not ranks:
        raise ValueError("ranks must contain at least one parameter")
    if set(ranks) != set(draw_counts):
        raise ValueError("ranks and draw_counts must have identical parameter keys")
    level = float(alpha)
    if not math.isfinite(level) or not 0.0 < level < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    n_sim = int(simulations)
    if n_sim < 100:
        raise ValueError("simulations must be at least 100")
    n_points = int(evaluation_points)
    if n_points < 3:
        raise ValueError("evaluation_points must be at least 3")
    grid = tuple((index + 1) / (n_points + 1) for index in range(n_points))

    clean_ranks: dict[str, tuple[int, ...]] = {}
    clean_counts: dict[str, tuple[int, ...]] = {}
    for parameter in ranks:
        parameter_ranks = tuple(int(value) for value in ranks[parameter])
        parameter_counts = tuple(int(value) for value in draw_counts[parameter])
        if not parameter_ranks or len(parameter_ranks) != len(parameter_counts):
            raise ValueError("each parameter needs equally sized non-empty rank/support vectors")
        if any(count < 1 for count in parameter_counts):
            raise ValueError("draw counts must be positive")
        if any(rank < 0 or rank > count for rank, count in zip(parameter_ranks, parameter_counts)):
            raise ValueError("each SBC rank must lie in 0..its replicate draw_count")
        clean_ranks[parameter] = parameter_ranks
        clean_counts[parameter] = parameter_counts

    observed = {
        parameter: _parameter_max_deviation(
            clean_ranks[parameter], clean_counts[parameter], grid
        )
        for parameter in clean_ranks
    }
    observed_max = max(observed.values())

    rng = random.Random(int(seed))
    null_maxima: list[float] = []
    for _ in range(n_sim):
        family_max = 0.0
        for parameter in clean_ranks:
            supports = clean_counts[parameter]
            simulated_ranks = tuple(rng.randint(0, count) for count in supports)
            family_max = max(
                family_max,
                _parameter_max_deviation(simulated_ranks, supports, grid),
            )
        null_maxima.append(family_max)
    null_maxima.sort()
    # Conservative Monte Carlo order statistic for the familywise 1-alpha envelope.
    index = min(
        n_sim - 1,
        max(0, int(math.ceil((1.0 - level) * (n_sim + 1))) - 1),
    )
    critical = null_maxima[index]
    return SBCSimultaneousECDFResult(
        passed=bool(observed_max <= critical),
        alpha=level,
        simulations=n_sim,
        evaluation_grid=grid,
        critical_max_deviation=critical,
        observed_max_deviation=observed_max,
        parameter_max_deviation=observed,
    )
