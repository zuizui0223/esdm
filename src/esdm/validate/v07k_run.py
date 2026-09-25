"""Local burned-pilot re-optimization under population shift for v0.7k."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import V07G_DYNAMIC_TARGETS, V07G_SELECTED_PLACEMENT
from .v07i_selector import (
    _score_placement,
    select_v07i_placement_from_theta,
    theta_from_posterior_means,
)
from .v07k_fixture import truth_sites_for_v07k_world
from .v07k_fixture import (
    V07K_ORACLE_PLACEMENTS,
    V07K_WORLDS,
    build_v07k_confirm_fixture,
    build_v07k_local_pilot_fixture,
)


@dataclass(frozen=True, slots=True)
class V07KReplicate:
    world: str
    replicate: int
    pilot_seed: int
    confirm_seed: int
    adaptive_placement: tuple[int, ...]
    pilot_predicted_adaptive_to_transferred_ratio: float
    pilot_divergences: int
    adaptive_posterior_sds: dict
    transferred_posterior_sds: dict
    adaptive_posterior_means: dict
    adaptive_posterior_lows: dict
    adaptive_posterior_highs: dict
    adaptive_heldout_log_score: float
    transferred_heldout_log_score: float
    adaptive_divergences: int
    transferred_divergences: int

    def __post_init__(self) -> None:
        world = str(self.world)
        if world not in V07K_WORLDS:
            raise ValueError(f"unknown v0.7k world {world!r}")
        object.__setattr__(self, "world", world)
        placement = tuple(int(day) for day in self.adaptive_placement)
        if len(placement) != 4 or len(set(placement)) != 4:
            raise ValueError("v0.7k adaptive placement must have four unique days")
        object.__setattr__(self, "adaptive_placement", placement)

        expected = set(V07B_TRUTH)
        for name in (
            "adaptive_posterior_sds",
            "transferred_posterior_sds",
            "adaptive_posterior_means",
            "adaptive_posterior_lows",
            "adaptive_posterior_highs",
        ):
            values = {
                str(key): float(value)
                for key, value in getattr(self, name).items()
            }
            if set(values) != expected:
                raise ValueError(f"{name} targets must match v0.7k targets")
            object.__setattr__(self, name, MappingProxyType(values))

    @property
    def adaptive_worst_dynamic_sd(self) -> float:
        return max(
            self.adaptive_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def transferred_worst_dynamic_sd(self) -> float:
        return max(
            self.transferred_posterior_sds[target]
            for target in V07G_DYNAMIC_TARGETS
        )

    @property
    def worst_sd_ratio(self) -> float:
        return self.adaptive_worst_dynamic_sd / self.transferred_worst_dynamic_sd

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.adaptive_heldout_log_score)
            - float(self.transferred_heldout_log_score)
        )

    def adaptive_covers_truth(self, target: str) -> bool:
        truth = truth_sites_for_v07k_world(self.world)[target]
        return (
            self.adaptive_posterior_lows[target]
            <= truth
            <= self.adaptive_posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V07KWorldSummary:
    world: str
    replicates: int
    fit_count: int
    adaptive_lower_worst_sd_rate: float
    mean_worst_sd_ratio: float
    minimum_ratio: float
    maximum_ratio: float
    mean_pilot_predicted_ratio: float
    oracle_placement_selection_rate: float
    selection_counts: dict
    adaptive_mean_biases: dict
    adaptive_coverages: dict
    positive_heldout_gain_rate: float
    mean_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07KSummary:
    worlds: dict
    replicates: int
    fit_count: int
    total_divergences: int


def _pilot_data(generated_counts, fixture):
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.source.source.joint_train_keys
            }
        },
        "pilot_calibration": {
            "sp": {
                key: int(generated_counts["pilot_calibration"]["sp"][key])
                for key in fixture.pilot_keys
            }
        },
    }


def _confirm_data(generated_counts, fixture, *, adaptive: bool):
    stream_name = "adaptive_calibration" if adaptive else "transferred_calibration"
    keys = fixture.adaptive_keys if adaptive else fixture.transferred_keys
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.source.joint_train_keys
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


def run_v07k_replicate(
    *,
    world: str,
    replicate: int,
    pilot_seed: int,
    confirm_seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07KReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    name = str(world)
    if name not in V07K_WORLDS:
        raise KeyError(f"unknown v0.7k world {name!r}")
    if int(pilot_seed) == int(confirm_seed):
        raise ValueError("pilot and confirmatory seeds must be disjoint")

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }

    pilot = build_v07k_local_pilot_fixture(name)
    pilot_generated = simulate_observations(
        pilot.generator_model,
        pilot.generating_theta,
        pilot.covariates,
        theta_obs=pilot.generating_theta_obs,
        seed=int(pilot_seed),
    )
    pilot_fit = fit_numpyro(
        pilot.training_model,
        _pilot_data(pilot_generated.counts, pilot),
        pilot.covariates,
        rng_seed=int(pilot_seed) + 1,
        **fit_kwargs,
    )
    pilot_theta = theta_from_posterior_means(pilot_fit.samples)
    selection = select_v07i_placement_from_theta(pilot_theta)
    transferred_score = _score_placement(
        V07G_SELECTED_PLACEMENT,
        theta=pilot_theta,
    )
    predicted_ratio = (
        selection.selected.worst_dynamic_sd
        / transferred_score.worst_dynamic_sd
    )

    confirm = build_v07k_confirm_fixture(
        name,
        selection.selected.placement,
    )
    generated = simulate_observations(
        confirm.generator_model,
        confirm.generating_theta,
        confirm.covariates,
        theta_obs=confirm.generating_theta_obs,
        seed=int(confirm_seed),
    )
    adaptive_fit = fit_numpyro(
        confirm.adaptive_model,
        _confirm_data(generated.counts, confirm, adaptive=True),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 1,
        **fit_kwargs,
    )
    transferred_fit = fit_numpyro(
        confirm.transferred_model,
        _confirm_data(generated.counts, confirm, adaptive=False),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 2,
        **fit_kwargs,
    )

    adaptive_sds = {}
    transferred_sds = {}
    means = {}
    lows = {}
    highs = {}
    alpha = (1.0 - float(credible_mass)) / 2.0
    for target in V07B_TRUTH:
        adaptive_draws = tuple(
            float(value) for value in adaptive_fit.samples[target]
        )
        transferred_draws = tuple(
            float(value) for value in transferred_fit.samples[target]
        )
        adaptive_sds[target] = _posterior_sd(adaptive_draws)
        transferred_sds[target] = _posterior_sd(transferred_draws)
        means[target] = math.fsum(adaptive_draws) / len(adaptive_draws)
        lows[target] = _quantile(adaptive_draws, alpha)
        highs[target] = _quantile(adaptive_draws, 1.0 - alpha)

    return V07KReplicate(
        world=name,
        replicate=int(replicate),
        pilot_seed=int(pilot_seed),
        confirm_seed=int(confirm_seed),
        adaptive_placement=selection.selected.placement,
        pilot_predicted_adaptive_to_transferred_ratio=float(predicted_ratio),
        pilot_divergences=pilot_fit.num_divergences,
        adaptive_posterior_sds=adaptive_sds,
        transferred_posterior_sds=transferred_sds,
        adaptive_posterior_means=means,
        adaptive_posterior_lows=lows,
        adaptive_posterior_highs=highs,
        adaptive_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            adaptive_fit.samples,
            confirm.covariates,
            generated.counts,
            confirm.heldout_keys,
        ),
        transferred_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            transferred_fit.samples,
            confirm.covariates,
            generated.counts,
            confirm.heldout_keys,
        ),
        adaptive_divergences=adaptive_fit.num_divergences,
        transferred_divergences=transferred_fit.num_divergences,
    )


def _summarize_world(world: str, rows) -> V07KWorldSummary:
    selected = tuple(row for row in rows if row.world == world)
    truth = truth_sites_for_v07k_world(world)
    ratios = tuple(row.worst_sd_ratio for row in selected)
    predicted = tuple(
        row.pilot_predicted_adaptive_to_transferred_ratio
        for row in selected
    )
    gains = tuple(row.heldout_gain for row in selected)

    counts = {}
    for row in selected:
        key = ",".join(str(day) for day in row.adaptive_placement)
        counts[key] = counts.get(key, 0) + 1

    biases = {}
    coverages = {}
    for target in V07B_TRUTH:
        biases[target] = math.fsum(
            row.adaptive_posterior_means[target] - truth[target]
            for row in selected
        ) / len(selected)
        coverages[target] = sum(
            row.adaptive_covers_truth(target) for row in selected
        ) / len(selected)

    return V07KWorldSummary(
        world=world,
        replicates=len(selected),
        fit_count=3 * len(selected),
        adaptive_lower_worst_sd_rate=sum(
            row.adaptive_worst_dynamic_sd
            < row.transferred_worst_dynamic_sd
            for row in selected
        ) / len(selected),
        mean_worst_sd_ratio=math.fsum(ratios) / len(ratios),
        minimum_ratio=min(ratios),
        maximum_ratio=max(ratios),
        mean_pilot_predicted_ratio=math.fsum(predicted) / len(predicted),
        oracle_placement_selection_rate=sum(
            row.adaptive_placement == V07K_ORACLE_PLACEMENTS[world]
            for row in selected
        ) / len(selected),
        selection_counts=dict(sorted(counts.items())),
        adaptive_mean_biases=biases,
        adaptive_coverages=coverages,
        positive_heldout_gain_rate=sum(gain > 0.0 for gain in gains)
        / len(gains),
        mean_heldout_gain=math.fsum(gains) / len(gains),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in selected
        ),
    )


def summarize_v07k(records: Sequence[V07KReplicate]) -> V07KSummary:
    rows = tuple(records)
    worlds = {
        world: _summarize_world(world, rows)
        for world in V07K_WORLDS
    }
    return V07KSummary(
        worlds=worlds,
        replicates=len(rows),
        fit_count=3 * len(rows),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in rows
        ),
    )
