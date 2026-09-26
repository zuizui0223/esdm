"""Selective burned-pilot adaptation under fresh population shift for v0.7l."""
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
from .v07l_fixture import (
    V07L_TRIGGER_RATIO,
    V07L_WORLDS,
    build_v07l_confirm_fixture,
    build_v07l_local_pilot_fixture,
    truth_sites_for_v07l_world,
)


@dataclass(frozen=True, slots=True)
class V07LReplicate:
    world: str
    replicate: int
    pilot_seed: int
    confirm_seed: int
    adaptive_placement: tuple[int, ...]
    pilot_predicted_adaptive_to_transferred_ratio: float
    policy_action: str
    pilot_divergences: int
    adaptive_posterior_sds: dict
    transferred_posterior_sds: dict
    adaptive_posterior_means: dict
    adaptive_posterior_lows: dict
    adaptive_posterior_highs: dict
    transferred_posterior_means: dict
    transferred_posterior_lows: dict
    transferred_posterior_highs: dict
    adaptive_heldout_log_score: float
    transferred_heldout_log_score: float
    adaptive_divergences: int
    transferred_divergences: int

    def __post_init__(self) -> None:
        world = str(self.world)
        if world not in V07L_WORLDS:
            raise ValueError(f"unknown v0.7l world {world!r}")
        object.__setattr__(self, "world", world)
        placement = tuple(int(day) for day in self.adaptive_placement)
        if len(placement) != 4 or len(set(placement)) != 4:
            raise ValueError("v0.7l adaptive placement must have four unique days")
        object.__setattr__(self, "adaptive_placement", placement)
        action = str(self.policy_action)
        if action not in {"adaptive", "transferred"}:
            raise ValueError("v0.7l policy_action must be adaptive or transferred")
        expected_action = (
            "adaptive"
            if float(self.pilot_predicted_adaptive_to_transferred_ratio)
            <= V07L_TRIGGER_RATIO
            else "transferred"
        )
        if action != expected_action:
            raise ValueError(
                "v0.7l policy_action disagrees with frozen pilot trigger"
            )
        object.__setattr__(self, "policy_action", action)

        expected = set(V07B_TRUTH)
        for name in (
            "adaptive_posterior_sds",
            "transferred_posterior_sds",
            "adaptive_posterior_means",
            "adaptive_posterior_lows",
            "adaptive_posterior_highs",
            "transferred_posterior_means",
            "transferred_posterior_lows",
            "transferred_posterior_highs",
        ):
            values = {
                str(key): float(value)
                for key, value in getattr(self, name).items()
            }
            if set(values) != expected:
                raise ValueError(f"{name} targets must match v0.7l targets")
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
    def actual_ratio(self) -> float:
        return self.adaptive_worst_dynamic_sd / self.transferred_worst_dynamic_sd

    @property
    def predicted_trigger(self) -> bool:
        return self.pilot_predicted_adaptive_to_transferred_ratio <= V07L_TRIGGER_RATIO

    @property
    def actual_material_headroom(self) -> bool:
        return self.actual_ratio <= V07L_TRIGGER_RATIO

    @property
    def policy_to_transferred_ratio(self) -> float:
        return self.actual_ratio if self.policy_action == "adaptive" else 1.0

    @property
    def oracle_threshold_ratio(self) -> float:
        return self.actual_ratio if self.actual_material_headroom else 1.0

    @property
    def policy_regret(self) -> float:
        return self.policy_to_transferred_ratio - self.oracle_threshold_ratio

    @property
    def policy_heldout_log_score(self) -> float:
        if self.policy_action == "adaptive":
            return float(self.adaptive_heldout_log_score)
        return float(self.transferred_heldout_log_score)

    @property
    def adaptive_minus_transferred_heldout_gain(self) -> float:
        return (
            float(self.adaptive_heldout_log_score)
            - float(self.transferred_heldout_log_score)
        )

    def policy_mean(self, target: str) -> float:
        if self.policy_action == "adaptive":
            return self.adaptive_posterior_means[target]
        return self.transferred_posterior_means[target]

    def policy_covers_truth(self, target: str) -> bool:
        truth = truth_sites_for_v07l_world(self.world)[target]
        if self.policy_action == "adaptive":
            low = self.adaptive_posterior_lows[target]
            high = self.adaptive_posterior_highs[target]
        else:
            low = self.transferred_posterior_lows[target]
            high = self.transferred_posterior_highs[target]
        return low <= truth <= high


@dataclass(frozen=True, slots=True)
class V07LWorldSummary:
    world: str
    replicates: int
    fit_count: int
    trigger_rate: float
    actual_material_headroom_rate: float
    trigger_correct_rate: float
    mean_predicted_ratio: float
    mean_actual_ratio: float
    mean_policy_to_transferred_ratio: float
    policy_harm_rate: float
    mean_policy_regret: float
    policy_mean_biases: dict
    policy_coverages: dict
    mean_adaptive_minus_transferred_heldout_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07LSummary:
    worlds: dict
    replicates: int
    fit_count: int
    trigger_true_positive: int
    trigger_false_positive: int
    trigger_true_negative: int
    trigger_false_negative: int
    trigger_sensitivity: float
    trigger_specificity: float
    trigger_balanced_accuracy: float
    mean_policy_to_transferred_ratio: float
    policy_harm_rate: float
    mean_policy_regret: float
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


def _posterior_summary(samples, *, credible_mass: float):
    alpha = (1.0 - float(credible_mass)) / 2.0
    means = {}
    lows = {}
    highs = {}
    sds = {}
    for target in V07B_TRUTH:
        draws = tuple(float(value) for value in samples[target])
        means[target] = math.fsum(draws) / len(draws)
        lows[target] = _quantile(draws, alpha)
        highs[target] = _quantile(draws, 1.0 - alpha)
        sds[target] = _posterior_sd(draws)
    return means, lows, highs, sds


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


def run_v07l_replicate(
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
) -> V07LReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    name = str(world)
    if name not in V07L_WORLDS:
        raise KeyError(f"unknown v0.7l world {name!r}")
    if int(pilot_seed) == int(confirm_seed):
        raise ValueError("pilot and confirmatory seeds must be disjoint")

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }

    pilot = build_v07l_local_pilot_fixture(name)
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
    action = "adaptive" if predicted_ratio <= V07L_TRIGGER_RATIO else "transferred"

    confirm = build_v07l_confirm_fixture(
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

    a_means, a_lows, a_highs, a_sds = _posterior_summary(
        adaptive_fit.samples,
        credible_mass=credible_mass,
    )
    t_means, t_lows, t_highs, t_sds = _posterior_summary(
        transferred_fit.samples,
        credible_mass=credible_mass,
    )

    return V07LReplicate(
        world=name,
        replicate=int(replicate),
        pilot_seed=int(pilot_seed),
        confirm_seed=int(confirm_seed),
        adaptive_placement=selection.selected.placement,
        pilot_predicted_adaptive_to_transferred_ratio=float(predicted_ratio),
        policy_action=action,
        pilot_divergences=pilot_fit.num_divergences,
        adaptive_posterior_sds=a_sds,
        transferred_posterior_sds=t_sds,
        adaptive_posterior_means=a_means,
        adaptive_posterior_lows=a_lows,
        adaptive_posterior_highs=a_highs,
        transferred_posterior_means=t_means,
        transferred_posterior_lows=t_lows,
        transferred_posterior_highs=t_highs,
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


def _mean(values) -> float:
    rows = tuple(float(value) for value in values)
    return math.fsum(rows) / len(rows)


def _summarize_world(world: str, rows) -> V07LWorldSummary:
    selected = tuple(row for row in rows if row.world == world)
    truth = truth_sites_for_v07l_world(world)
    if not selected:
        raise ValueError(f"v0.7l world {world!r} has no records")

    biases = {}
    coverages = {}
    for target in V07B_TRUTH:
        biases[target] = _mean(
            row.policy_mean(target) - truth[target]
            for row in selected
        )
        coverages[target] = _mean(
            1.0 if row.policy_covers_truth(target) else 0.0
            for row in selected
        )

    return V07LWorldSummary(
        world=world,
        replicates=len(selected),
        fit_count=3 * len(selected),
        trigger_rate=_mean(
            1.0 if row.predicted_trigger else 0.0 for row in selected
        ),
        actual_material_headroom_rate=_mean(
            1.0 if row.actual_material_headroom else 0.0
            for row in selected
        ),
        trigger_correct_rate=_mean(
            1.0
            if row.predicted_trigger == row.actual_material_headroom
            else 0.0
            for row in selected
        ),
        mean_predicted_ratio=_mean(
            row.pilot_predicted_adaptive_to_transferred_ratio
            for row in selected
        ),
        mean_actual_ratio=_mean(row.actual_ratio for row in selected),
        mean_policy_to_transferred_ratio=_mean(
            row.policy_to_transferred_ratio for row in selected
        ),
        policy_harm_rate=_mean(
            1.0 if row.policy_to_transferred_ratio > 1.0 else 0.0
            for row in selected
        ),
        mean_policy_regret=_mean(row.policy_regret for row in selected),
        policy_mean_biases=biases,
        policy_coverages=coverages,
        mean_adaptive_minus_transferred_heldout_gain=_mean(
            row.adaptive_minus_transferred_heldout_gain
            for row in selected
        ),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in selected
        ),
    )


def summarize_v07l(records: Sequence[V07LReplicate]) -> V07LSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7l records must be non-empty")
    worlds = {
        world: _summarize_world(world, rows)
        for world in V07L_WORLDS
    }

    tp = sum(row.predicted_trigger and row.actual_material_headroom for row in rows)
    fp = sum(row.predicted_trigger and not row.actual_material_headroom for row in rows)
    tn = sum((not row.predicted_trigger) and (not row.actual_material_headroom) for row in rows)
    fn = sum((not row.predicted_trigger) and row.actual_material_headroom for row in rows)
    sensitivity = tp / (tp + fn) if (tp + fn) else 1.0
    specificity = tn / (tn + fp) if (tn + fp) else 1.0

    return V07LSummary(
        worlds=worlds,
        replicates=len(rows),
        fit_count=3 * len(rows),
        trigger_true_positive=tp,
        trigger_false_positive=fp,
        trigger_true_negative=tn,
        trigger_false_negative=fn,
        trigger_sensitivity=float(sensitivity),
        trigger_specificity=float(specificity),
        trigger_balanced_accuracy=float(0.5 * (sensitivity + specificity)),
        mean_policy_to_transferred_ratio=_mean(
            row.policy_to_transferred_ratio for row in rows
        ),
        policy_harm_rate=_mean(
            1.0 if row.policy_to_transferred_ratio > 1.0 else 0.0
            for row in rows
        ),
        mean_policy_regret=_mean(row.policy_regret for row in rows),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.adaptive_divergences)
            + int(row.transferred_divergences)
            for row in rows
        ),
    )
