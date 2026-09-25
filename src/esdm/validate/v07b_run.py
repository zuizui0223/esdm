"""Replicated recovery and late-time transfer for frozen v0.7b."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile
from .v07b_fixture import V07B_TRUTH, build_v07b_fixture


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
        truth = float(V07B_TRUTH[target])
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


def _training_data(generated_counts, fixture):
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.joint_train_keys
            }
        },
        "occupancy_calibration": {
            "sp": {
                key: int(
                    generated_counts["occupancy_calibration"]["sp"][key]
                )
                for key in fixture.direct_train_keys
            }
        },
    }


def _heldout_joint_log_predictive_density(
    model,
    samples,
    covariates,
    generated_counts,
    heldout_keys,
):
    from esdm.model.backend_numpyro import posterior_observation_rates

    rates_by_block = posterior_observation_rates(model, samples, covariates)
    block_name = "joint.sp"
    if block_name not in rates_by_block:
        raise KeyError(f"posterior rates missing {block_name!r}")
    draws = tuple(rates_by_block[block_name])
    keys = tuple(model.domain.keys)
    index_by_key = {key: index for index, key in enumerate(keys)}
    if not draws:
        raise ValueError("posterior joint rates require at least one draw")

    scores = []
    for key in heldout_keys:
        index = index_by_key[key]
        count = int(generated_counts["joint"]["sp"][key])
        scores.append(
            _logmeanexp(
                _poisson_log_mass(count, draw[index])
                for draw in draws
            )
        )
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
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_data = _training_data(generated.counts, fixture)

    full_train = fixture.training_model
    knockout_train = fixture.training_model.knockout("sp", "occupancy")
    full_score_model = fixture.scoring_model
    knockout_score_model = fixture.scoring_model.knockout("sp", "occupancy")

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    full_fit = fit_numpyro(
        full_train,
        train_data,
        fixture.covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    knockout_fit = fit_numpyro(
        knockout_train,
        train_data,
        fixture.covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    means = {}
    lows = {}
    highs = {}
    for target in V07B_TRUTH:
        draws = tuple(float(value) for value in full_fit.samples[target])
        means[target] = math.fsum(draws) / len(draws)
        lows[target] = _quantile(draws, alpha)
        highs[target] = _quantile(draws, 1.0 - alpha)

    full_score = _heldout_joint_log_predictive_density(
        full_score_model,
        full_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )
    knockout_score = _heldout_joint_log_predictive_density(
        knockout_score_model,
        knockout_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )

    return V07BReplicate(
        replicate=int(replicate),
        posterior_means=means,
        posterior_lows=lows,
        posterior_highs=highs,
        full_heldout_log_score=full_score,
        occupancy_knockout_heldout_log_score=knockout_score,
        full_divergences=full_fit.num_divergences,
        knockout_divergences=knockout_fit.num_divergences,
    )


def summarize_v07b(records: Sequence[V07BReplicate]) -> V07BSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7b records must be non-empty")
    n = len(rows)
    mean_biases = {}
    coverages = {}
    for target, truth in V07B_TRUTH.items():
        mean_biases[target] = math.fsum(
            row.posterior_means[target] - float(truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.covers_truth(target)
            for row in rows
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
    )
