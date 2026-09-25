"""Fresh MCMC confirmation of v0.7j population-shift transfer and reversal."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import V07G_DYNAMIC_TARGETS
from .v07j_confirm import (
    V07J_WORLDS,
    build_v07j_confirm_fixture,
    truth_sites_for_v07j_world,
)


@dataclass(frozen=True, slots=True)
class V07JReplicate:
    world: str
    replicate: int
    selected_posterior_sds: dict
    baseline_posterior_sds: dict
    winner_posterior_means: dict
    winner_posterior_lows: dict
    winner_posterior_highs: dict
    selected_heldout_log_score: float
    baseline_heldout_log_score: float
    selected_divergences: int
    baseline_divergences: int

    def __post_init__(self) -> None:
        world = str(self.world)
        if world not in V07J_WORLDS:
            raise ValueError(f"unknown v0.7j world {world!r}")
        object.__setattr__(self, "world", world)
        expected = set(V07B_TRUTH)
        for name in (
            "selected_posterior_sds",
            "baseline_posterior_sds",
            "winner_posterior_means",
            "winner_posterior_lows",
            "winner_posterior_highs",
        ):
            values = {
                str(key): float(value)
                for key, value in getattr(self, name).items()
            }
            if set(values) != expected:
                raise ValueError(
                    f"{name} targets must match v0.7j recovery targets"
                )
            object.__setattr__(self, name, MappingProxyType(values))

    @property
    def selected_worst_dynamic_sd(self) -> float:
        return max(
            self.selected_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def baseline_worst_dynamic_sd(self) -> float:
        return max(
            self.baseline_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def selected_to_baseline_ratio(self) -> float:
        return self.selected_worst_dynamic_sd / self.baseline_worst_dynamic_sd

    @property
    def correct_direction(self) -> bool:
        if self.world == "transfer_positive":
            return self.selected_to_baseline_ratio < 1.0
        return self.selected_to_baseline_ratio > 1.0

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.selected_heldout_log_score)
            - float(self.baseline_heldout_log_score)
        )

    def winner_covers_truth(self, target: str) -> bool:
        truth = truth_sites_for_v07j_world(self.world)[target]
        return (
            self.winner_posterior_lows[target]
            <= truth
            <= self.winner_posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V07JWorldSummary:
    world: str
    replicates: int
    fit_count: int
    correct_direction_rate: float
    mean_selected_to_baseline_ratio: float
    minimum_ratio: float
    maximum_ratio: float
    winner_mean_biases: dict
    winner_coverages: dict
    positive_heldout_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07JSummary:
    worlds: dict
    replicates: int
    fit_count: int
    total_divergences: int


def _candidate_data(generated_counts, fixture, *, selected: bool):
    stream_name = (
        "selected_calibration" if selected else "baseline_calibration"
    )
    keys = fixture.selected_keys if selected else fixture.baseline_keys
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.source.source.joint_train_keys
            }
        },
        stream_name: {
            "sp": {
                key: int(generated_counts[stream_name]["sp"][key])
                for key in keys
            }
        },
    }


def _posterior_sd(values) -> float:
    rows = tuple(float(value) for value in values)
    mean = math.fsum(rows) / len(rows)
    return math.sqrt(
        math.fsum((value - mean) ** 2 for value in rows) / len(rows)
    )


def _heldout_score(model, samples, covariates, generated_counts, heldout_keys):
    from esdm.model.backend_numpyro import posterior_observation_rates

    draws = tuple(
        posterior_observation_rates(model, samples, covariates)["joint.sp"]
    )
    keys = tuple(model.domain.keys)
    index_by_key = {key: index for index, key in enumerate(keys)}
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


def run_v07j_replicate(
    *,
    world: str,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07JReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07j_confirm_fixture(world)
    generated = simulate_observations(
        fixture.generator_model,
        fixture.generating_theta,
        fixture.covariates,
        theta_obs=fixture.generating_theta_obs,
        seed=int(seed),
    )
    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }
    selected_fit = fit_numpyro(
        fixture.selected_model,
        _candidate_data(generated.counts, fixture, selected=True),
        fixture.covariates,
        rng_seed=int(seed) + 1,
        **fit_kwargs,
    )
    baseline_fit = fit_numpyro(
        fixture.baseline_model,
        _candidate_data(generated.counts, fixture, selected=False),
        fixture.covariates,
        rng_seed=int(seed) + 2,
        **fit_kwargs,
    )

    selected_sds = {}
    baseline_sds = {}
    for target in V07B_TRUTH:
        selected_sds[target] = _posterior_sd(selected_fit.samples[target])
        baseline_sds[target] = _posterior_sd(baseline_fit.samples[target])

    winner_fit = (
        selected_fit if str(world) == "transfer_positive" else baseline_fit
    )
    alpha = (1.0 - float(credible_mass)) / 2.0
    means = {}
    lows = {}
    highs = {}
    for target in V07B_TRUTH:
        draws = tuple(float(value) for value in winner_fit.samples[target])
        means[target] = math.fsum(draws) / len(draws)
        lows[target] = _quantile(draws, alpha)
        highs[target] = _quantile(draws, 1.0 - alpha)

    return V07JReplicate(
        world=str(world),
        replicate=int(replicate),
        selected_posterior_sds=selected_sds,
        baseline_posterior_sds=baseline_sds,
        winner_posterior_means=means,
        winner_posterior_lows=lows,
        winner_posterior_highs=highs,
        selected_heldout_log_score=_heldout_score(
            fixture.scoring_model,
            selected_fit.samples,
            fixture.covariates,
            generated.counts,
            fixture.heldout_keys,
        ),
        baseline_heldout_log_score=_heldout_score(
            fixture.scoring_model,
            baseline_fit.samples,
            fixture.covariates,
            generated.counts,
            fixture.heldout_keys,
        ),
        selected_divergences=selected_fit.num_divergences,
        baseline_divergences=baseline_fit.num_divergences,
    )


def _summarize_world(world: str, rows) -> V07JWorldSummary:
    selected = tuple(row for row in rows if row.world == world)
    truth = truth_sites_for_v07j_world(world)
    ratios = tuple(row.selected_to_baseline_ratio for row in selected)
    gains = tuple(row.heldout_gain for row in selected)
    biases = {}
    coverages = {}
    for target in V07B_TRUTH:
        biases[target] = math.fsum(
            row.winner_posterior_means[target] - truth[target]
            for row in selected
        ) / len(selected)
        coverages[target] = sum(
            row.winner_covers_truth(target) for row in selected
        ) / len(selected)
    return V07JWorldSummary(
        world=world,
        replicates=len(selected),
        fit_count=2 * len(selected),
        correct_direction_rate=sum(
            row.correct_direction for row in selected
        ) / len(selected),
        mean_selected_to_baseline_ratio=math.fsum(ratios) / len(ratios),
        minimum_ratio=min(ratios),
        maximum_ratio=max(ratios),
        winner_mean_biases=biases,
        winner_coverages=coverages,
        positive_heldout_gain_rate=sum(gain > 0.0 for gain in gains) / len(gains),
        mean_heldout_gain=math.fsum(gains) / len(gains),
        total_divergences=sum(
            int(row.selected_divergences) + int(row.baseline_divergences)
            for row in selected
        ),
    )


def summarize_v07j(records: Sequence[V07JReplicate]) -> V07JSummary:
    rows = tuple(records)
    worlds = {
        world: _summarize_world(world, rows)
        for world in V07J_WORLDS
    }
    return V07JSummary(
        worlds=worlds,
        replicates=len(rows),
        fit_count=2 * len(rows),
        total_divergences=sum(
            int(row.selected_divergences) + int(row.baseline_divergences)
            for row in rows
        ),
    )
