"""Replicated matched static-versus-dynamic held-out comparison for v0.7c."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass
from .v07c_fixture import build_v07c_fixture


@dataclass(frozen=True, slots=True)
class V07CReplicate:
    replicate: int
    dynamic_heldout_log_score: float
    static_heldout_log_score: float
    dynamic_divergences: int
    static_divergences: int

    @property
    def dynamic_gain(self) -> float:
        return (
            float(self.dynamic_heldout_log_score)
            - float(self.static_heldout_log_score)
        )


@dataclass(frozen=True, slots=True)
class V07CSummary:
    replicates: int
    fit_count: int
    dynamic_better_rate: float
    mean_dynamic_gain: float
    minimum_dynamic_gain: float
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


def _heldout_score(
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


def run_v07c_replicate(
    *,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07CReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07c_fixture()
    generated = simulate_observations(
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    train_data = _training_data(generated.counts, fixture)

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    dynamic_fit = fit_numpyro(
        fixture.dynamic_training_model,
        train_data,
        fixture.covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    static_fit = fit_numpyro(
        fixture.static_training_model,
        train_data,
        fixture.covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    dynamic_score = _heldout_score(
        fixture.dynamic_scoring_model,
        dynamic_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )
    static_score = _heldout_score(
        fixture.static_scoring_model,
        static_fit.samples,
        fixture.covariates,
        generated.counts,
        fixture.heldout_keys,
    )

    return V07CReplicate(
        replicate=int(replicate),
        dynamic_heldout_log_score=dynamic_score,
        static_heldout_log_score=static_score,
        dynamic_divergences=dynamic_fit.num_divergences,
        static_divergences=static_fit.num_divergences,
    )


def summarize_v07c(records: Sequence[V07CReplicate]) -> V07CSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7c records must be non-empty")
    n = len(rows)
    gains = tuple(row.dynamic_gain for row in rows)
    return V07CSummary(
        replicates=n,
        fit_count=2 * n,
        dynamic_better_rate=sum(gain > 0.0 for gain in gains) / n,
        mean_dynamic_gain=math.fsum(gains) / n,
        minimum_dynamic_gain=min(gains),
        total_divergences=sum(
            int(row.dynamic_divergences) + int(row.static_divergences)
            for row in rows
        ),
    )
