"""Replicated recovery and held-out accessibility transfer for v0.6a."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_run import (
    _logmeanexp,
    _poisson_log_mass,
    _quantile,
    _subset_data,
)
from .v06a_fixture import V06A_RECOVERY_TRUTH, build_v06a_fixture


@dataclass(frozen=True, slots=True)
class V06AReplicate:
    replicate: int
    posterior_means: dict
    posterior_lows: dict
    posterior_highs: dict
    full_heldout_log_score: float
    accessibility_knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    @property
    def accessibility_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.accessibility_knockout_heldout_log_score)
        )

    def covers_truth(self, target: str) -> bool:
        truth = float(V06A_RECOVERY_TRUTH[target])
        return (
            float(self.posterior_lows[target])
            <= truth
            <= float(self.posterior_highs[target])
        )


@dataclass(frozen=True, slots=True)
class V06ASummary:
    replicates: int
    fit_count: int
    mean_biases: dict
    coverages: dict
    positive_gain_rate: float
    mean_gain: float
    minimum_gain: float
    total_divergences: int


def _subset_model(fixture, spaces, *, knockout: bool):
    grid = Grid(
        space=tuple(spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    model = Model(
        domain=grid,
        species=fixture.model.species,
        streams=fixture.model.streams,
    )
    if knockout:
        model = model.knockout("sp", "accessibility")
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    model.check_design()
    return model, covariates


def _joint_log_predictive_density(model, samples, covariates, data):
    from esdm.model.backend_numpyro import posterior_observation_rates

    if "joint" not in data or "sp" not in data["joint"]:
        raise KeyError("missing held-out joint data for sp")
    rates_by_block = posterior_observation_rates(model, samples, covariates)
    block_name = "joint.sp"
    if block_name not in rates_by_block:
        raise KeyError(f"posterior rates missing {block_name!r}")
    draws = tuple(rates_by_block[block_name])
    keys = tuple(model.domain.keys)
    counts_map = data["joint"]["sp"]
    scores = []
    for index, key in enumerate(keys):
        count = int(counts_map[key])
        scores.append(
            _logmeanexp(
                _poisson_log_mass(count, draw[index])
                for draw in draws
            )
        )
    return math.fsum(scores) / len(scores)


def run_v06a_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V06AReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v06a_fixture()
    generated = simulate_observations(
        fixture.model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )

    full_train, train_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=False
    )
    knockout_train, knockout_cov = _subset_model(
        fixture, fixture.train_spaces, knockout=True
    )
    full_heldout, heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=False
    )
    knockout_heldout, knockout_heldout_cov = _subset_model(
        fixture, fixture.heldout_spaces, knockout=True
    )

    full_data = _subset_data(generated.counts, full_train)
    knockout_data = _subset_data(generated.counts, knockout_train)
    heldout_data = _subset_data(generated.counts, full_heldout)

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    full_fit = fit_numpyro(
        full_train,
        full_data,
        train_cov,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    knockout_fit = fit_numpyro(
        knockout_train,
        knockout_data,
        knockout_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    means = {}
    lows = {}
    highs = {}
    for target in V06A_RECOVERY_TRUTH:
        draws = tuple(float(value) for value in full_fit.samples[target])
        means[target] = math.fsum(draws) / len(draws)
        lows[target] = _quantile(draws, alpha)
        highs[target] = _quantile(draws, 1.0 - alpha)

    full_score = _joint_log_predictive_density(
        full_heldout,
        full_fit.samples,
        heldout_cov,
        heldout_data,
    )
    knockout_score = _joint_log_predictive_density(
        knockout_heldout,
        knockout_fit.samples,
        knockout_heldout_cov,
        heldout_data,
    )

    return V06AReplicate(
        replicate=int(replicate),
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=full_score,
        accessibility_knockout_heldout_log_score=knockout_score,
        full_divergences=full_fit.num_divergences,
        knockout_divergences=knockout_fit.num_divergences,
    )


def summarize_v06a(records: Sequence[V06AReplicate]) -> V06ASummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.6a records must be non-empty")
    n = len(rows)
    mean_biases = {}
    coverages = {}
    for target, truth in V06A_RECOVERY_TRUTH.items():
        mean_biases[target] = math.fsum(
            row.posterior_means[target] - float(truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.covers_truth(target) for row in rows
        ) / n
    gains = tuple(row.accessibility_gain for row in rows)
    return V06ASummary(
        replicates=n,
        fit_count=2 * n,
        mean_biases=mean_biases,
        coverages=coverages,
        positive_gain_rate=sum(gain > 0.0 for gain in gains) / n,
        mean_gain=math.fsum(gains) / n,
        minimum_gain=min(gains),
        total_divergences=sum(
            int(row.full_divergences) + int(row.knockout_divergences)
            for row in rows
        ),
    )
