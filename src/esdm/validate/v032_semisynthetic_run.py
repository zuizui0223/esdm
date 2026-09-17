"""Outcome-producing runner for the already-frozen v0.3.2 Gate F-prime profile."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_presence_only
from .evidence import compare_knockout
from .v032_semisynthetic import build_v032_semisynthetic_fixture
from .v032_semisynthetic_gate import (
    V032SemiSyntheticSummary,
    evaluate_v032_identification_profiles,
)


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticReplicate:
    replicate: int
    beta_precip_mean: float
    beta_precip_low: float
    beta_precip_high: float
    gamma_precip_mean: float
    gamma_precip_low: float
    gamma_precip_high: float
    beta_eastness_mean: float
    beta_eastness_low: float
    beta_eastness_high: float
    full_heldout_log_score: float
    knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    @property
    def heldout_gain(self) -> float:
        return self.full_heldout_log_score - self.knockout_heldout_log_score

    @property
    def beta_precip_covers_truth(self) -> bool:
        return self.beta_precip_low <= 0.45 <= self.beta_precip_high

    @property
    def gamma_precip_covers_truth(self) -> bool:
        return self.gamma_precip_low <= 0.40 <= self.gamma_precip_high

    @property
    def beta_eastness_covers_truth(self) -> bool:
        return self.beta_eastness_low <= 0.35 <= self.beta_eastness_high


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticResult:
    replicates: tuple[V032SemiSyntheticReplicate, ...]
    summary: V032SemiSyntheticSummary
    train_space_count: int
    heldout_space_count: int


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


def _subset_model(fixture, spaces: Sequence[str], *, knockout: bool):
    grid = Grid(
        space=tuple(str(space) for space in spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    source_process = fixture.model.species["sp"][0]
    process = source_process.knockout() if knockout else source_process
    model = Model(
        domain=grid,
        species={"sp": (process,)},
        streams=fixture.model.streams,
    )
    covariates = {key: dict(fixture.covariates[key]) for key in grid.keys}
    return model, covariates


def _subset_data(generated_counts, model: Model):
    output = {}
    for stream in model.streams:
        output[stream.name] = {}
        for species in model.stream_targets(stream):
            source = generated_counts[stream.name][species]
            output[stream.name][species] = {
                key: int(source[key]) for key in model.domain.keys
            }
    return output


def summarize_v032_semisynthetic(
    records: Sequence[V032SemiSyntheticReplicate],
    *,
    identification,
    extrapolation_integrity: bool,
) -> V032SemiSyntheticSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.3.2 semi-synthetic records must be non-empty")
    n = len(rows)
    return V032SemiSyntheticSummary(
        replicates=n,
        positive_structural_pass=identification.positive_structural_pass,
        positive_practical_pass=identification.positive_practical_pass,
        negative_structural_pass=identification.negative_structural_pass,
        negative_practical_refused=identification.negative_practical_refused,
        extrapolation_integrity=bool(extrapolation_integrity),
        beta_precip_mean_bias=sum(row.beta_precip_mean - 0.45 for row in rows) / n,
        gamma_precip_mean_bias=sum(row.gamma_precip_mean - 0.40 for row in rows) / n,
        beta_eastness_mean_bias=sum(row.beta_eastness_mean - 0.35 for row in rows) / n,
        beta_precip_coverage=sum(row.beta_precip_covers_truth for row in rows) / n,
        gamma_precip_coverage=sum(row.gamma_precip_covers_truth for row in rows) / n,
        beta_eastness_coverage=sum(row.beta_eastness_covers_truth for row in rows) / n,
        positive_gain_rate=sum(row.heldout_gain > 0.0 for row in rows) / n,
        mean_heldout_gain=sum(row.heldout_gain for row in rows) / n,
        total_divergences=sum(
            int(row.full_divergences) + int(row.knockout_divergences)
            for row in rows
        ),
        fit_count=2 * n,
    )


def run_v032_semisynthetic_benchmark(
    source_csv_text: str,
    *,
    replicates: int = 20,
    base_seed: int = 20260922,
    num_warmup: int = 250,
    num_samples: int = 300,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V032SemiSyntheticResult:
    """Run the positive-profile outcome benchmark under frozen semantics."""

    from esdm.model.backend_numpyro import fit_numpyro

    n_rep = int(replicates)
    if n_rep < 1:
        raise ValueError("replicates must be positive")
    mass = float(credible_mass)
    if not 0.0 < mass < 1.0:
        raise ValueError("credible_mass must be in (0, 1)")

    fixture = build_v032_semisynthetic_fixture(source_csv_text, profile="positive")
    identification = evaluate_v032_identification_profiles(source_csv_text)
    full_train, train_covariates = _subset_model(fixture, fixture.train_spaces, knockout=False)
    knockout_train, knockout_train_covariates = _subset_model(
        fixture, fixture.train_spaces, knockout=True
    )
    full_heldout, heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=False
    )
    knockout_heldout, knockout_heldout_covariates = _subset_model(
        fixture, fixture.heldout_spaces, knockout=True
    )

    train_max = max(
        fixture.covariates[(space, fixture.model.domain.doy[0], fixture.model.domain.hour[0])][
            "eastness_z_train"
        ]
        for space in fixture.train_spaces
    )
    heldout_min = min(
        fixture.covariates[(space, fixture.model.domain.doy[0], fixture.model.domain.hour[0])][
            "eastness_z_train"
        ]
        for space in fixture.heldout_spaces
    )
    extrapolation_integrity = heldout_min > train_max

    alpha = (1.0 - mass) / 2.0
    records = []
    for replicate in range(n_rep):
        seed = int(base_seed) + replicate * 41
        generated = simulate_presence_only(
            fixture.model,
            fixture.generating_theta,
            fixture.covariates,
            theta_obs=fixture.generating_theta_obs,
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
            target_accept_prob=float(target_accept_prob),
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
            target_accept_prob=float(target_accept_prob),
        )

        beta = tuple(float(x) for x in full_fit.samples["sp.suitability.beta_precip"])
        gamma = tuple(float(x) for x in full_fit.samples["stream.opportunistic.gamma_precip"])
        eastness = tuple(float(x) for x in full_fit.samples["sp.suitability.beta_eastness"])
        comparison = compare_knockout(
            full_heldout,
            full_fit.samples,
            knockout_heldout,
            knockout_fit.samples,
            full_covariates=heldout_covariates,
            knockout_covariates=knockout_heldout_covariates,
            data=heldout_data,
            stream_name="opportunistic",
            species="sp",
        )
        records.append(
            V032SemiSyntheticReplicate(
                replicate=replicate,
                beta_precip_mean=sum(beta) / len(beta),
                beta_precip_low=_quantile(beta, alpha),
                beta_precip_high=_quantile(beta, 1.0 - alpha),
                gamma_precip_mean=sum(gamma) / len(gamma),
                gamma_precip_low=_quantile(gamma, alpha),
                gamma_precip_high=_quantile(gamma, 1.0 - alpha),
                beta_eastness_mean=sum(eastness) / len(eastness),
                beta_eastness_low=_quantile(eastness, alpha),
                beta_eastness_high=_quantile(eastness, 1.0 - alpha),
                full_heldout_log_score=comparison.full_log_score,
                knockout_heldout_log_score=comparison.knockout_log_score,
                full_divergences=full_fit.num_divergences,
                knockout_divergences=knockout_fit.num_divergences,
            )
        )

    record_tuple = tuple(records)
    summary = summarize_v032_semisynthetic(
        record_tuple,
        identification=identification,
        extrapolation_integrity=extrapolation_integrity,
    )
    return V032SemiSyntheticResult(
        replicates=record_tuple,
        summary=summary,
        train_space_count=len(fixture.train_spaces),
        heldout_space_count=len(fixture.heldout_spaces),
    )
