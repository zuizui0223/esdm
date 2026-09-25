"""Burned-pilot adaptive calibration-placement validation for v0.7i."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass, _quantile
from .v07b_fixture import V07B_TRUTH
from .v07g_fixture import V07G_DYNAMIC_TARGETS, V07G_SELECTED_PLACEMENT
from .v07i_fixture import (
    build_v07i_confirm_fixture,
    build_v07i_pilot_fixture,
)
from .v07i_selector import (
    select_v07i_placement_from_theta,
    theta_from_posterior_means,
)


@dataclass(frozen=True, slots=True)
class V07IReplicate:
    replicate: int
    pilot_seed: int
    confirm_seed: int
    selected_placement: tuple[int, ...]
    pilot_predicted_sd_ratio: float
    pilot_divergences: int
    selected_posterior_sds: dict
    baseline_posterior_sds: dict
    selected_posterior_means: dict
    selected_posterior_lows: dict
    selected_posterior_highs: dict
    selected_heldout_log_score: float
    baseline_heldout_log_score: float
    selected_divergences: int
    baseline_divergences: int

    def __post_init__(self) -> None:
        placement = tuple(int(value) for value in self.selected_placement)
        if len(placement) != 4 or len(set(placement)) != 4:
            raise ValueError("v0.7i selected placement must contain four unique days")
        object.__setattr__(self, "selected_placement", placement)

        expected = set(V07B_TRUTH)
        for name in (
            "selected_posterior_sds",
            "baseline_posterior_sds",
            "selected_posterior_means",
            "selected_posterior_lows",
            "selected_posterior_highs",
        ):
            values = {
                str(key): float(value)
                for key, value in getattr(self, name).items()
            }
            if set(values) != expected:
                raise ValueError(f"{name} targets must match frozen v0.7i targets")
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
    def worst_sd_ratio(self) -> float:
        return self.selected_worst_dynamic_sd / self.baseline_worst_dynamic_sd

    @property
    def heldout_gain(self) -> float:
        return (
            float(self.selected_heldout_log_score)
            - float(self.baseline_heldout_log_score)
        )

    def selected_covers_truth(self, target: str) -> bool:
        truth = float(V07B_TRUTH[target])
        return (
            self.selected_posterior_lows[target]
            <= truth
            <= self.selected_posterior_highs[target]
        )


@dataclass(frozen=True, slots=True)
class V07ISummary:
    replicates: int
    fit_count: int
    selected_lower_worst_sd_rate: float
    mean_worst_sd_ratio: float
    minimum_worst_sd_ratio: float
    maximum_worst_sd_ratio: float
    mean_pilot_predicted_sd_ratio: float
    oracle_placement_selection_rate: float
    selection_counts: dict
    selected_mean_biases: dict
    selected_coverages: dict
    positive_heldout_gain_rate: float
    mean_heldout_gain: float
    minimum_heldout_gain: float
    total_divergences: int


def _pilot_data(generated_counts, fixture):
    return {
        "joint": {
            "sp": {
                key: int(generated_counts["joint"]["sp"][key])
                for key in fixture.source.joint_train_keys
            }
        },
        "pilot_calibration": {
            "sp": {
                key: int(generated_counts["pilot_calibration"]["sp"][key])
                for key in fixture.pilot_keys
            }
        },
    }


def _confirm_data(generated_counts, fixture, *, selected: bool):
    stream_name = (
        "selected_calibration" if selected else "baseline_calibration"
    )
    keys = fixture.selected_keys if selected else fixture.baseline_keys
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
    if not rows:
        raise ValueError("posterior SD requires at least one draw")
    mean = math.fsum(rows) / len(rows)
    return math.sqrt(
        math.fsum((value - mean) ** 2 for value in rows) / len(rows)
    )


def _heldout_score(model, samples, covariates, generated_counts, heldout_keys):
    from esdm.model.backend_numpyro import posterior_observation_rates

    rates_by_block = posterior_observation_rates(model, samples, covariates)
    draws = tuple(rates_by_block["joint.sp"])
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


def run_v07i_replicate(
    *,
    replicate: int,
    pilot_seed: int,
    confirm_seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    credible_mass: float = 0.90,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07IReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    if int(pilot_seed) == int(confirm_seed):
        raise ValueError("v0.7i pilot and confirmatory seeds must be disjoint")

    fit_kwargs = {
        "num_warmup": int(num_warmup),
        "num_samples": int(num_samples),
        "num_chains": int(num_chains),
        "progress_bar": bool(progress_bar),
        "target_accept_prob": float(target_accept_prob),
    }

    pilot = build_v07i_pilot_fixture()
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

    confirm = build_v07i_confirm_fixture(selection.selected.placement)
    confirm_generated = simulate_observations(
        confirm.generator_model,
        confirm.generating_theta,
        confirm.covariates,
        theta_obs=confirm.generating_theta_obs,
        seed=int(confirm_seed),
    )

    selected_fit = fit_numpyro(
        confirm.selected_model,
        _confirm_data(confirm_generated.counts, confirm, selected=True),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 1,
        **fit_kwargs,
    )
    baseline_fit = fit_numpyro(
        confirm.baseline_model,
        _confirm_data(confirm_generated.counts, confirm, selected=False),
        confirm.covariates,
        rng_seed=int(confirm_seed) + 2,
        **fit_kwargs,
    )

    alpha = (1.0 - float(credible_mass)) / 2.0
    selected_sds = {}
    baseline_sds = {}
    means = {}
    lows = {}
    highs = {}
    for target in V07B_TRUTH:
        selected_draws = tuple(
            float(value) for value in selected_fit.samples[target]
        )
        baseline_draws = tuple(
            float(value) for value in baseline_fit.samples[target]
        )
        selected_sds[target] = _posterior_sd(selected_draws)
        baseline_sds[target] = _posterior_sd(baseline_draws)
        means[target] = math.fsum(selected_draws) / len(selected_draws)
        lows[target] = _quantile(selected_draws, alpha)
        highs[target] = _quantile(selected_draws, 1.0 - alpha)

    return V07IReplicate(
        replicate=int(replicate),
        pilot_seed=int(pilot_seed),
        confirm_seed=int(confirm_seed),
        selected_placement=selection.selected.placement,
        pilot_predicted_sd_ratio=(
            selection.selected_to_baseline_predicted_ratio
        ),
        pilot_divergences=pilot_fit.num_divergences,
        selected_posterior_sds=selected_sds,
        baseline_posterior_sds=baseline_sds,
        selected_posterior_means=means,
        selected_posterior_lows=lows,
        selected_posterior_highs=highs,
        selected_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            selected_fit.samples,
            confirm.covariates,
            confirm_generated.counts,
            confirm.heldout_keys,
        ),
        baseline_heldout_log_score=_heldout_score(
            confirm.scoring_model,
            baseline_fit.samples,
            confirm.covariates,
            confirm_generated.counts,
            confirm.heldout_keys,
        ),
        selected_divergences=selected_fit.num_divergences,
        baseline_divergences=baseline_fit.num_divergences,
    )


def summarize_v07i(records: Sequence[V07IReplicate]) -> V07ISummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7i records must be non-empty")
    n = len(rows)
    ratios = tuple(row.worst_sd_ratio for row in rows)
    predicted = tuple(row.pilot_predicted_sd_ratio for row in rows)
    gains = tuple(row.heldout_gain for row in rows)

    mean_biases = {}
    coverages = {}
    for target, truth in V07B_TRUTH.items():
        mean_biases[target] = math.fsum(
            row.selected_posterior_means[target] - float(truth)
            for row in rows
        ) / n
        coverages[target] = sum(
            row.selected_covers_truth(target)
            for row in rows
        ) / n

    counts = {}
    for row in rows:
        key = ",".join(str(day) for day in row.selected_placement)
        counts[key] = counts.get(key, 0) + 1

    return V07ISummary(
        replicates=n,
        fit_count=3 * n,
        selected_lower_worst_sd_rate=sum(
            row.selected_worst_dynamic_sd
            < row.baseline_worst_dynamic_sd
            for row in rows
        ) / n,
        mean_worst_sd_ratio=math.fsum(ratios) / n,
        minimum_worst_sd_ratio=min(ratios),
        maximum_worst_sd_ratio=max(ratios),
        mean_pilot_predicted_sd_ratio=math.fsum(predicted) / n,
        oracle_placement_selection_rate=sum(
            row.selected_placement == V07G_SELECTED_PLACEMENT
            for row in rows
        ) / n,
        selection_counts=dict(sorted(counts.items())),
        selected_mean_biases=mean_biases,
        selected_coverages=coverages,
        positive_heldout_gain_rate=sum(gain > 0.0 for gain in gains) / n,
        mean_heldout_gain=math.fsum(gains) / n,
        minimum_heldout_gain=min(gains),
        total_divergences=sum(
            int(row.pilot_divergences)
            + int(row.selected_divergences)
            + int(row.baseline_divergences)
            for row in rows
        ),
    )
