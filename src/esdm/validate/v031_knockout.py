"""v0.3.1 neutral-suitability knockout benchmark.

Unlike the retired v0.3 knockout, this control preserves baseline abundance and the
observation-effort geometry. Only the environmental slope is neutralized.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability
from esdm.simulate import simulate_presence_only


@dataclass(frozen=True, slots=True)
class V031NeutralKnockoutWorld:
    generating_model: Model
    fitting_model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    generating_theta: Mapping[str, Mapping[str, float]]
    truth: float = 0.0
    target_parameter: str = "sp.suitability.beta_x"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {key: MappingProxyType(dict(values)) for key, values in self.covariates.items()}
            ),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType(
                {species: MappingProxyType(dict(values)) for species, values in self.generating_theta.items()}
            ),
        )


@dataclass(frozen=True, slots=True)
class V031KnockoutReplicate:
    replicate: int
    posterior_mean: float
    interval_low: float
    interval_high: float
    num_divergences: int

    @property
    def covers_zero(self) -> bool:
        return self.interval_low <= 0.0 <= self.interval_high

    @property
    def nonzero(self) -> bool:
        return self.interval_low > 0.0 or self.interval_high < 0.0


@dataclass(frozen=True, slots=True)
class V031KnockoutSummary:
    replicates: int
    mean_posterior: float
    zero_coverage: float
    nonzero_rate: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V031KnockoutResult:
    replicates: tuple[V031KnockoutReplicate, ...]
    summary: V031KnockoutSummary


@dataclass(frozen=True, slots=True)
class V031KnockoutGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V031KnockoutGateConfig:
    replicates: int = 100
    max_abs_mean: float = 0.10
    min_zero_coverage: float = 0.82
    max_zero_coverage: float = 0.98
    max_nonzero_rate: float = 0.12
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V031KnockoutGateDecision:
    passed: bool
    checks: tuple[V031KnockoutGateCheck, ...]


def _quantile(values, probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("posterior draws must be non-empty")
    p = float(probability)
    if not 0.0 <= p <= 1.0:
        raise ValueError("quantile probability must be in [0, 1]")
    if len(ordered) == 1:
        return ordered[0]
    position = p * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def make_v031_neutral_knockout_world() -> V031NeutralKnockoutWorld:
    """Build the frozen neutral-slope control with baseline intensity preserved."""

    x = tuple(-1.875 + 0.25 * i for i in range(16))
    grid = Grid(space=tuple(f"s{i:02d}" for i in range(len(x))), doy=(1,), hour=(0,))
    covariates = {
        key: {"x": float(x[index])}
        for index, key in enumerate(grid.keys)
    }
    # Non-monotone effort geometry prevents effort from being a disguised x slope.
    effort_pattern = (5.0, 8.0, 4.0, 9.0, 6.0, 3.0, 7.0, 5.0)
    effort_values = tuple(effort_pattern[i % len(effort_pattern)] for i in range(len(x)))
    effort = EffortField(
        {
            key: effort_values[index]
            for index, key in enumerate(grid.keys)
        }
    )
    process = LinearSuitability(
        covariates=("x",),
        intercept_parameter="intercept",
        coefficient_parameters={"x": "beta_x"},
    )
    stream = PresenceOnly(
        name="records",
        effort=effort,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    fitting_model = Model(
        domain=grid,
        species={"sp": (process,)},
        streams=(stream,),
    )
    generating_model = fitting_model.knockout("sp", "suitability")
    return V031NeutralKnockoutWorld(
        generating_model=generating_model,
        fitting_model=fitting_model,
        covariates=covariates,
        generating_theta={"sp": {"intercept": 2.0}},
    )


def summarize_v031_knockout(
    records: tuple[V031KnockoutReplicate, ...] | list[V031KnockoutReplicate],
) -> V031KnockoutSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("knockout records must be non-empty")
    n = len(rows)
    return V031KnockoutSummary(
        replicates=n,
        mean_posterior=sum(row.posterior_mean for row in rows) / n,
        zero_coverage=sum(row.covers_zero for row in rows) / n,
        nonzero_rate=sum(row.nonzero for row in rows) / n,
        total_divergences=sum(int(row.num_divergences) for row in rows),
    )


def run_v031_knockout_benchmark(
    *,
    replicates: int,
    base_seed: int = 20260920,
    num_warmup: int = 250,
    num_samples: int = 300,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
) -> V031KnockoutResult:
    """Repeatedly simulate the neutral world and fit the full suitability model."""

    from esdm.model.backend_numpyro import fit_numpyro

    n_rep = int(replicates)
    if n_rep < 1:
        raise ValueError("replicates must be positive")
    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    world = make_v031_neutral_knockout_world()
    alpha = (1.0 - mass) / 2.0
    rows: list[V031KnockoutReplicate] = []
    for replicate in range(n_rep):
        seed = int(base_seed) + replicate * 31
        generated = simulate_presence_only(
            world.generating_model,
            world.generating_theta,
            world.covariates,
            seed=seed,
        )
        fit = fit_numpyro(
            world.fitting_model,
            generated.counts,
            world.covariates,
            rng_seed=seed + 1,
            num_warmup=int(num_warmup),
            num_samples=int(num_samples),
            num_chains=int(num_chains),
            progress_bar=bool(progress_bar),
        )
        draws = tuple(float(value) for value in fit.samples[world.target_parameter])
        rows.append(
            V031KnockoutReplicate(
                replicate=replicate,
                posterior_mean=sum(draws) / len(draws),
                interval_low=_quantile(draws, alpha),
                interval_high=_quantile(draws, 1.0 - alpha),
                num_divergences=fit.num_divergences,
            )
        )
    records = tuple(rows)
    return V031KnockoutResult(records, summarize_v031_knockout(records))


def evaluate_v031_knockout_gate(
    summary: V031KnockoutSummary,
    *,
    config: V031KnockoutGateConfig | None = None,
) -> V031KnockoutGateDecision:
    """Mechanically evaluate frozen Gate C thresholds."""

    cfg = V031KnockoutGateConfig() if config is None else config
    mean_divergences = (
        summary.total_divergences / summary.replicates
        if summary.replicates
        else float("inf")
    )
    checks = (
        V031KnockoutGateCheck(
            "knockout_replicates",
            summary.replicates == cfg.replicates,
            summary.replicates,
            f"replicates == {cfg.replicates}",
        ),
        V031KnockoutGateCheck(
            "knockout_mean",
            abs(summary.mean_posterior) <= cfg.max_abs_mean,
            summary.mean_posterior,
            f"abs(mean posterior beta) <= {cfg.max_abs_mean}",
        ),
        V031KnockoutGateCheck(
            "knockout_zero_coverage",
            cfg.min_zero_coverage <= summary.zero_coverage <= cfg.max_zero_coverage,
            summary.zero_coverage,
            f"zero coverage in [{cfg.min_zero_coverage}, {cfg.max_zero_coverage}]",
        ),
        V031KnockoutGateCheck(
            "knockout_nonzero_rate",
            summary.nonzero_rate <= cfg.max_nonzero_rate,
            summary.nonzero_rate,
            f"nonzero interval rate <= {cfg.max_nonzero_rate}",
        ),
        V031KnockoutGateCheck(
            "knockout_divergences",
            mean_divergences <= cfg.max_mean_divergences_per_fit,
            mean_divergences,
            f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
        ),
    )
    return V031KnockoutGateDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
