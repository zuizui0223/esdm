"""Replicated budget-matched evidence comparison for v0.6c."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile, _subset_data
from .v06a_fixture import V06A_RECOVERY_TRUTH
from .v06c_fixture import (
    V06C_ACCESS_TARGETS,
    build_v06c_fixture,
    v06c_condition_model,
)


def _sample_sd(values):
    rows = tuple(float(value) for value in values)
    if len(rows) < 2:
        raise ValueError("posterior SD requires at least two draws")
    mean = math.fsum(rows) / len(rows)
    return math.sqrt(
        math.fsum((value - mean) ** 2 for value in rows)
        / (len(rows) - 1)
    )


@dataclass(frozen=True, slots=True)
class V06CReplicate:
    replicate: int
    direct_means: dict
    matched_means: dict
    direct_sds: dict
    matched_sds: dict
    direct_lows: dict
    direct_highs: dict
    matched_lows: dict
    matched_highs: dict
    direct_aux_count: int
    matched_aux_count: int
    direct_heldout_log_score: float
    matched_heldout_log_score: float
    direct_divergences: int
    matched_divergences: int

    def direct_covers(self, target):
        truth = float(V06A_RECOVERY_TRUTH[target])
        return self.direct_lows[target] <= truth <= self.direct_highs[target]

    def matched_covers(self, target):
        truth = float(V06A_RECOVERY_TRUTH[target])
        return self.matched_lows[target] <= truth <= self.matched_highs[target]


@dataclass(frozen=True, slots=True)
class V06CSummary:
    replicates: int
    fit_count: int
    direct_mean_biases: dict
    matched_mean_biases: dict
    direct_coverages: dict
    matched_coverages: dict
    direct_lower_sd_rates: dict
    mean_sd_ratios: dict
    mean_direct_aux_count: float
    mean_matched_aux_count: float
    mean_heldout_gain_direct_minus_matched: float
    direct_better_heldout_rate: float
    total_divergences: int


def _base_joint_log_predictive_density(model, samples, covariates, data):
    from esdm.model.backend_numpyro import posterior_observation_rates

    rates_by_block = posterior_observation_rates(model, samples, covariates)
    draws = tuple(rates_by_block["base_joint.sp"])
    keys = tuple(model.domain.keys)
    counts = data["base_joint"]["sp"]
    scores = []
    for index, key in enumerate(keys):
        value = int(counts[key])
        scores.append(
            _logmeanexp(
                _poisson_log_mass(value, draw[index])
                for draw in draws
            )
        )
    return math.fsum(scores) / len(scores)


def _total_counts(generated, stream):
    return sum(
        int(value)
        for value in generated.counts[stream]["sp"].values()
    )


def run_v06c_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V06CReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v06c_fixture()
    generated = simulate_observations(
        fixture.model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    direct_model, direct_cov = v06c_condition_model(
        fixture, "direct", fixture.train_spaces
    )
    matched_model, matched_cov = v06c_condition_model(
        fixture, "matched_joint", fixture.train_spaces
    )
    heldout_model, heldout_cov = v06c_condition_model(
        fixture, "heldout", fixture.heldout_spaces
    )

    direct_data = _subset_data(generated.counts, direct_model)
    matched_data = _subset_data(generated.counts, matched_model)
    heldout_data = _subset_data(generated.counts, heldout_model)

    kwargs = dict(
        num_warmup=int(num_warmup),
        num_samples=int(num_samples),
        num_chains=int(num_chains),
        progress_bar=bool(progress_bar),
        target_accept_prob=float(target_accept_prob),
    )
    direct_fit = fit_numpyro(
        direct_model,
        direct_data,
        direct_cov,
        rng_seed=int(seed) + 1,
        **kwargs,
    )
    matched_fit = fit_numpyro(
        matched_model,
        matched_data,
        matched_cov,
        rng_seed=int(seed) + 2,
        **kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    direct_means = {}
    matched_means = {}
    direct_sds = {}
    matched_sds = {}
    direct_lows = {}
    direct_highs = {}
    matched_lows = {}
    matched_highs = {}

    for target in V06A_RECOVERY_TRUTH:
        direct_draws = tuple(float(x) for x in direct_fit.samples[target])
        matched_draws = tuple(float(x) for x in matched_fit.samples[target])
        direct_means[target] = math.fsum(direct_draws) / len(direct_draws)
        matched_means[target] = math.fsum(matched_draws) / len(matched_draws)
        direct_sds[target] = _sample_sd(direct_draws)
        matched_sds[target] = _sample_sd(matched_draws)
        direct_lows[target] = _quantile(direct_draws, alpha)
        direct_highs[target] = _quantile(direct_draws, 1.0 - alpha)
        matched_lows[target] = _quantile(matched_draws, alpha)
        matched_highs[target] = _quantile(matched_draws, 1.0 - alpha)

    direct_score = _base_joint_log_predictive_density(
        heldout_model, direct_fit.samples, heldout_cov, heldout_data
    )
    matched_score = _base_joint_log_predictive_density(
        heldout_model, matched_fit.samples, heldout_cov, heldout_data
    )

    return V06CReplicate(
        replicate=int(replicate),
        direct_means=direct_means,
        matched_means=matched_means,
        direct_sds=direct_sds,
        matched_sds=matched_sds,
        direct_lows=direct_lows,
        direct_highs=direct_highs,
        matched_lows=matched_lows,
        matched_highs=matched_highs,
        direct_aux_count=_total_counts(generated, "direct_access"),
        matched_aux_count=_total_counts(generated, "matched_joint"),
        direct_heldout_log_score=direct_score,
        matched_heldout_log_score=matched_score,
        direct_divergences=direct_fit.num_divergences,
        matched_divergences=matched_fit.num_divergences,
    )


def summarize_v06c(records: Sequence[V06CReplicate]) -> V06CSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.6c records must be non-empty")
    n = len(rows)
    direct_bias = {}
    matched_bias = {}
    direct_cov = {}
    matched_cov = {}
    lower_rates = {}
    ratios = {}

    for target, truth in V06A_RECOVERY_TRUTH.items():
        direct_bias[target] = math.fsum(
            row.direct_means[target] - float(truth) for row in rows
        ) / n
        matched_bias[target] = math.fsum(
            row.matched_means[target] - float(truth) for row in rows
        ) / n
        direct_cov[target] = sum(row.direct_covers(target) for row in rows) / n
        matched_cov[target] = sum(row.matched_covers(target) for row in rows) / n

    for target in V06C_ACCESS_TARGETS:
        lower_rates[target] = sum(
            row.direct_sds[target] < row.matched_sds[target]
            for row in rows
        ) / n
        ratios[target] = math.fsum(
            row.direct_sds[target] / row.matched_sds[target]
            for row in rows
        ) / n

    gains = tuple(
        row.direct_heldout_log_score - row.matched_heldout_log_score
        for row in rows
    )
    return V06CSummary(
        replicates=n,
        fit_count=2 * n,
        direct_mean_biases=direct_bias,
        matched_mean_biases=matched_bias,
        direct_coverages=direct_cov,
        matched_coverages=matched_cov,
        direct_lower_sd_rates=lower_rates,
        mean_sd_ratios=ratios,
        mean_direct_aux_count=math.fsum(row.direct_aux_count for row in rows) / n,
        mean_matched_aux_count=math.fsum(row.matched_aux_count for row in rows) / n,
        mean_heldout_gain_direct_minus_matched=math.fsum(gains) / n,
        direct_better_heldout_rate=sum(gain > 0.0 for gain in gains) / n,
        total_divergences=sum(
            int(row.direct_divergences) + int(row.matched_divergences)
            for row in rows
        ),
    )
