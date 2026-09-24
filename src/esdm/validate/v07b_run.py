"""Frozen replicated recovery and held-out transfer for v0.7b."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.model import Model
from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile, _subset_data
from .v07b_fixture import (
    V07B_RECOVERY_TRUTH,
    build_v07b_fixture,
    full_trajectory_model,
    training_model,
)


@dataclass(frozen=True, slots=True)
class V07BReplicate:
    replicate: int
    posterior_means: dict
    posterior_lows: dict
    posterior_highs: dict
    full_heldout_log_score: float
    occupancy_knockout_heldout_log_score: float
    full_divergences: int
    knockout_divergences: int

    @property
    def occupancy_gain(self) -> float:
        return (
            float(self.full_heldout_log_score)
            - float(self.occupancy_knockout_heldout_log_score)
        )

    def covers_truth(self, target: str) -> bool:
        truth = float(V07B_RECOVERY_TRUTH[target])
        return (
            float(self.posterior_lows[target])
            <= truth
            <= float(self.posterior_highs[target])
        )


@dataclass(frozen=True, slots=True)
class V07BSummary:
    replicates: int
    fit_count: int
    mean_biases: dict
    coverages: dict
    positive_gain_rate: float
    mean_gain: float
    minimum_gain: float
    total_divergences: int
    mean_full_heldout_log_score: float
    mean_knockout_heldout_log_score: float


def _joint_log_predictive_density_on_keys(
    model: Model,
    samples,
    covariates,
    data,
    *,
    keys: Sequence[object],
) -> float:
    from esdm.model.backend_numpyro import posterior_observation_rates

    if "joint" not in data or "sp" not in data["joint"]:
        raise KeyError("missing joint data for sp")
    rates_by_block = posterior_observation_rates(model, samples, covariates)
    block_name = "joint.sp"
    if block_name not in rates_by_block:
        raise KeyError(f"posterior rates missing {block_name!r}")
    draws = tuple(rates_by_block[block_name])
    domain_keys = tuple(model.domain.keys)
    index = {key: position for position, key in enumerate(domain_keys)}
    counts = data["joint"]["sp"]
    scores = []
    for key in keys:
        if key not in index:
            raise KeyError(f"held-out key {key!r} absent from full prediction trajectory")
        value = int(counts[key])
        position = index[key]
        scores.append(
            _logmeanexp(
                _poisson_log_mass(value, draw[position])
                for draw in draws
            )
        )
    if not scores:
        raise ValueError("held-out key set must be non-empty")
    return math.fsum(scores) / len(scores)


def run_v07b_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07BReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07b_fixture()
    generated = simulate_observations(
        fixture.base.positive_model,
        fixture.base.theta,
        fixture.base.covariates,
        theta_obs=fixture.base.theta_obs_positive,
        seed=int(seed),
    )

    full_train, full_train_cov = training_model(fixture, knockout=False)
    knockout_train, knockout_train_cov = training_model(fixture, knockout=True)
    full_predict, full_predict_cov = full_trajectory_model(
        fixture, knockout=False
    )
    knockout_predict, knockout_predict_cov = full_trajectory_model(
        fixture, knockout=True
    )

    full_data = _subset_data(generated.counts, full_train)
    knockout_data = _subset_data(generated.counts, knockout_train)

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
        full_train_cov,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    knockout_fit = fit_numpyro(
        knockout_train,
        knockout_data,
        knockout_train_cov,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    means = {}
    lows = {}
    highs = {}
    for target in V07B_RECOVERY_TRUTH:
        draws = tuple(float(value) for value in full_fit.samples[target])
        means[target] = math.fsum(draws) / len(draws)
        lows[target] = _quantile(draws, alpha)
        highs[target] = _quantile(draws, 1.0 - alpha)

    full_score = _joint_log_predictive_density_on_keys(
        full_predict,
        full_fit.samples,
        full_predict_cov,
        generated.counts,
        keys=fixture.heldout_keys,
    )
    knockout_score = _joint_log_predictive_density_on_keys(
        knockout_predict,
        knockout_fit.samples,
        knockout_predict_cov,
        generated.counts,
        keys=fixture.heldout_keys,
    )

    return V07BReplicate(
        replicate=int(replicate),
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=float(full_score),
        occupancy_knockout_heldout_log_score=float(knockout_score),
        full_divergences=int(full_fit.num_divergences),
        knockout_divergences=int(knockout_fit.num_divergences),
    )


def summarize_v07b(records: Sequence[V07BReplicate]) -> V07BSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7b records must be non-empty")
    n = len(rows)
    mean_biases = {}
    coverages = {}
    for target, truth in V07B_RECOVERY_TRUTH.items():
        mean_biases[target] = math.fsum(
            row.posterior_means[target] - float(truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.covers_truth(target) for row in rows
        ) / n

    gains = tuple(row.occupancy_gain for row in rows)
    return V07BSummary(
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
        mean_full_heldout_log_score=math.fsum(
            float(row.full_heldout_log_score) for row in rows
        ) / n,
        mean_knockout_heldout_log_score=math.fsum(
            float(row.occupancy_knockout_heldout_log_score) for row in rows
        ) / n,
    )
