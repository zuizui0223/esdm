"""Frozen v0.3.1 Gate F semi-synthetic real-geometry transfer benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.simulate import simulate_presence_only
from esdm.validate.v031_semisynthetic import (
    V031SemiSyntheticFixture,
    build_v031_semisynthetic_fixture,
)


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticReplicate:
    replicate: int
    beta_precip_mean: float
    beta_precip_low: float
    beta_precip_high: float
    beta_lat_mean: float
    beta_lat_low: float
    beta_lat_high: float
    full_heldout_log_score: float
    knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    @property
    def heldout_gain(self) -> float:
        return self.full_heldout_log_score - self.knockout_heldout_log_score

    @property
    def beta_precip_covers_truth(self) -> bool:
        return self.beta_precip_low <= 0.55 <= self.beta_precip_high

    @property
    def beta_lat_covers_truth(self) -> bool:
        return self.beta_lat_low <= -0.25 <= self.beta_lat_high


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticSummary:
    replicates: int
    beta_precip_mean_bias: float
    beta_lat_mean_bias: float
    beta_precip_coverage: float
    beta_lat_coverage: float
    positive_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticResult:
    replicates: tuple[V031SemiSyntheticReplicate, ...]
    summary: V031SemiSyntheticSummary
    train_space_count: int
    heldout_space_count: int
    heldout_block: str


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticGateCheck:
    name: str
    passed: bool
    observed: object
    criterion: str


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticGateConfig:
    replicates: int = 20
    max_abs_beta_precip_bias: float = 0.15
    max_abs_beta_lat_bias: float = 0.15
    min_beta_precip_coverage: float = 0.75
    min_beta_lat_coverage: float = 0.75
    min_positive_gain_rate: float = 0.80
    min_mean_heldout_gain: float = 0.01
    max_mean_divergences_per_fit: float = 0.10


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticGateDecision:
    passed: bool
    checks: tuple[V031SemiSyntheticGateCheck, ...]


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


def _subset_model(
    fixture: V031SemiSyntheticFixture,
    spaces: Sequence[str],
    *,
    knockout: bool,
) -> tuple[Model, dict[tuple[str, int, int], dict[str, float]]]:
    selected_spaces = tuple(str(space) for space in spaces)
    if not selected_spaces:
        raise ValueError("model subset requires at least one spatial location")
    grid = Grid(
        space=selected_spaces,
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    source_process = fixture.model.species["sp"][0]
    process = source_process.knockout() if knockout else source_process
    source_stream = fixture.model.streams[0]
    effort = EffortField({key: source_stream.effort.at(key) for key in grid.keys})
    stream = PresenceOnly(
        name=source_stream.name,
        effort=effort,
        informs=source_stream.informs,
        detection_probability=source_stream.detection_probability,
        consumes=source_stream.consumes,
        targets=frozenset({"sp"}),
    )
    model = Model(domain=grid, species={"sp": (process,)}, streams=(stream,))
    covariates = {key: dict(fixture.covariates[key]) for key in grid.keys}
    return model, covariates


def _subset_data(generated_counts, model: Model):
    stream_name = model.streams[0].name
    full_counts = generated_counts[stream_name]["sp"]
    return {
        stream_name: {
            "sp": {key: int(full_counts[key]) for key in model.domain.keys}
        }
    }


def _logmeanexp(values: Sequence[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        raise ValueError("logmeanexp needs at least one value")
    maximum = max(rows)
    if maximum == -math.inf:
        return -math.inf
    return maximum + math.log(sum(math.exp(value - maximum) for value in rows) / len(rows))


def _poisson_log_mass(count: int, rate: float) -> float:
    y = int(count)
    lam = float(rate)
    if y < 0 or not math.isfinite(lam) or lam < 0.0:
        raise ValueError("invalid Poisson count/rate")
    if lam == 0.0:
        return 0.0 if y == 0 else -math.inf
    return y * math.log(lam) - lam - math.lgamma(y + 1.0)


def _heldout_log_predictive_density(
    model: Model,
    samples,
    covariates,
    data,
) -> float:
    from esdm.model.backend_numpyro import posterior_record_rates

    key = (model.streams[0].name, "sp")
    draws = posterior_record_rates(model, samples, covariates)[key]
    if not draws:
        raise ValueError("posterior predictive rates must contain draws")
    counts_map = data[model.streams[0].name]["sp"]
    ordered_counts = tuple(int(counts_map[context]) for context in model.domain.keys)
    context_scores: list[float] = []
    for index, count in enumerate(ordered_counts):
        context_scores.append(
            _logmeanexp(
                tuple(
                    _poisson_log_mass(count, rate_draw[index])
                    for rate_draw in draws
                )
            )
        )
    return sum(context_scores) / len(context_scores)


def summarize_v031_semisynthetic(
    records: Sequence[V031SemiSyntheticReplicate],
) -> V031SemiSyntheticSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("semi-synthetic records must be non-empty")
    n = len(rows)
    return V031SemiSyntheticSummary(
        replicates=n,
        beta_precip_mean_bias=sum(row.beta_precip_mean - 0.55 for row in rows) / n,
        beta_lat_mean_bias=sum(row.beta_lat_mean - (-0.25) for row in rows) / n,
        beta_precip_coverage=sum(row.beta_precip_covers_truth for row in rows) / n,
        beta_lat_coverage=sum(row.beta_lat_covers_truth for row in rows) / n,
        positive_gain_rate=sum(row.heldout_gain > 0.0 for row in rows) / n,
        mean_heldout_gain=sum(row.heldout_gain for row in rows) / n,
        total_divergences=sum(
            int(row.full_divergences) + int(row.knockout_divergences)
            for row in rows
        ),
    )


def run_v031_semisynthetic_benchmark(
    source_csv_text: str,
    *,
    replicates: int = 20,
    base_seed: int = 20260921,
    num_warmup: int = 200,
    num_samples: int = 250,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
) -> V031SemiSyntheticResult:
    """Run the frozen real-geometry train/east-heldout benchmark."""

    from esdm.model.backend_numpyro import fit_numpyro

    n_rep = int(replicates)
    if n_rep < 1:
        raise ValueError("replicates must be positive")
    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")
    fixture = build_v031_semisynthetic_fixture(source_csv_text)
    full_train, train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout=False
    )
    knockout_train, knockout_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout=True
    )
    full_heldout, heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=False
    )
    knockout_heldout, knockout_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=True
    )
    alpha = (1.0 - mass) / 2.0
    records: list[V031SemiSyntheticReplicate] = []
    for replicate in range(n_rep):
        seed = int(base_seed) + replicate * 37
        generated = simulate_presence_only(
            fixture.model,
            fixture.generating_theta,
            fixture.covariates,
            seed=seed,
        )
        train_data = _subset_data(generated.counts, full_train)
        heldout_data = _subset_data(generated.counts, full_heldout)
        full_fit = fit_numpyro(
            full_train,
            train_data,
            train_covariates,
            rng_seed=seed + 1,
            num_warmup=int(num_warmup),
            num_samples=int(num_samples),
            num_chains=int(num_chains),
            progress_bar=bool(progress_bar),
        )
        knockout_fit = fit_numpyro(
            knockout_train,
            train_data,
            knockout_train_covariates,
            rng_seed=seed + 2,
            num_warmup=int(num_warmup),
            num_samples=int(num_samples),
            num_chains=int(num_chains),
            progress_bar=bool(progress_bar),
        )
        beta_precip_draws = tuple(
            float(value) for value in full_fit.samples["sp.suitability.beta_precip"]
        )
        beta_lat_draws = tuple(
            float(value) for value in full_fit.samples["sp.suitability.beta_lat"]
        )
        records.append(
            V031SemiSyntheticReplicate(
                replicate=replicate,
                beta_precip_mean=sum(beta_precip_draws) / len(beta_precip_draws),
                beta_precip_low=_quantile(beta_precip_draws, alpha),
                beta_precip_high=_quantile(beta_precip_draws, 1.0 - alpha),
                beta_lat_mean=sum(beta_lat_draws) / len(beta_lat_draws),
                beta_lat_low=_quantile(beta_lat_draws, alpha),
                beta_lat_high=_quantile(beta_lat_draws, 1.0 - alpha),
                full_heldout_log_score=_heldout_log_predictive_density(
                    full_heldout,
                    full_fit.samples,
                    heldout_covariates,
                    heldout_data,
                ),
                knockout_heldout_log_score=_heldout_log_predictive_density(
                    knockout_heldout,
                    knockout_fit.samples,
                    knockout_heldout_covariates,
                    heldout_data,
                ),
                full_divergences=full_fit.num_divergences,
                knockout_divergences=knockout_fit.num_divergences,
            )
        )
    record_tuple = tuple(records)
    return V031SemiSyntheticResult(
        replicates=record_tuple,
        summary=summarize_v031_semisynthetic(record_tuple),
        train_space_count=len(fixture.train_spaces),
        heldout_space_count=len(fixture.heldout_spaces),
        heldout_block=fixture.heldout_block,
    )


def evaluate_v031_semisynthetic_gate(
    summary: V031SemiSyntheticSummary,
    *,
    config: V031SemiSyntheticGateConfig | None = None,
) -> V031SemiSyntheticGateDecision:
    """Mechanically evaluate the pre-outcome frozen Gate F thresholds."""

    cfg = V031SemiSyntheticGateConfig() if config is None else config
    mean_divergences = (
        summary.total_divergences / (2 * summary.replicates)
        if summary.replicates
        else float("inf")
    )
    checks = (
        V031SemiSyntheticGateCheck(
            "gate_f_replicates",
            summary.replicates == cfg.replicates,
            summary.replicates,
            f"replicates == {cfg.replicates}",
        ),
        V031SemiSyntheticGateCheck(
            "beta_precip_bias",
            abs(summary.beta_precip_mean_bias) <= cfg.max_abs_beta_precip_bias,
            summary.beta_precip_mean_bias,
            f"abs(mean bias) <= {cfg.max_abs_beta_precip_bias}",
        ),
        V031SemiSyntheticGateCheck(
            "beta_lat_bias",
            abs(summary.beta_lat_mean_bias) <= cfg.max_abs_beta_lat_bias,
            summary.beta_lat_mean_bias,
            f"abs(mean bias) <= {cfg.max_abs_beta_lat_bias}",
        ),
        V031SemiSyntheticGateCheck(
            "beta_precip_coverage",
            summary.beta_precip_coverage >= cfg.min_beta_precip_coverage,
            summary.beta_precip_coverage,
            f"coverage >= {cfg.min_beta_precip_coverage}",
        ),
        V031SemiSyntheticGateCheck(
            "beta_lat_coverage",
            summary.beta_lat_coverage >= cfg.min_beta_lat_coverage,
            summary.beta_lat_coverage,
            f"coverage >= {cfg.min_beta_lat_coverage}",
        ),
        V031SemiSyntheticGateCheck(
            "heldout_positive_gain_rate",
            summary.positive_gain_rate >= cfg.min_positive_gain_rate,
            summary.positive_gain_rate,
            f"positive heldout gain rate >= {cfg.min_positive_gain_rate}",
        ),
        V031SemiSyntheticGateCheck(
            "heldout_mean_gain",
            summary.mean_heldout_gain >= cfg.min_mean_heldout_gain,
            summary.mean_heldout_gain,
            f"mean heldout gain per context >= {cfg.min_mean_heldout_gain}",
        ),
        V031SemiSyntheticGateCheck(
            "gate_f_divergences",
            mean_divergences <= cfg.max_mean_divergences_per_fit,
            mean_divergences,
            f"mean divergences per fit <= {cfg.max_mean_divergences_per_fit}",
        ),
    )
    return V031SemiSyntheticGateDecision(
        passed=all(check.passed for check in checks),
        checks=checks,
    )
