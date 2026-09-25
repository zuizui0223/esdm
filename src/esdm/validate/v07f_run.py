"""Out-of-family bidirectional resolution benchmark for v0.7f."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from esdm.simulate import simulate_observations
from .v04_r2_run import _logmeanexp, _poisson_log_mass
from .v07f_fixture import V07F_WORLDS, build_v07f_fixture, generator_for_world


@dataclass(frozen=True, slots=True)
class V07FReplicate:
    world: str
    replicate: int
    dynamic_heldout_log_score: float
    static_heldout_log_score: float
    dynamic_divergences: int
    static_divergences: int

    def __post_init__(self) -> None:
        world = str(self.world)
        if world not in V07F_WORLDS:
            raise ValueError(f"unknown v0.7f world {world!r}")
        object.__setattr__(self, "world", world)

    @property
    def correct_gain(self) -> float:
        if self.world == "dynamic_like":
            return (
                float(self.dynamic_heldout_log_score)
                - float(self.static_heldout_log_score)
            )
        return (
            float(self.static_heldout_log_score)
            - float(self.dynamic_heldout_log_score)
        )


@dataclass(frozen=True, slots=True)
class V07FWorldSummary:
    world: str
    replicates: int
    fit_count: int
    correct_better_rate: float
    mean_correct_gain: float
    minimum_correct_gain: float
    total_divergences: int


@dataclass(frozen=True, slots=True)
class V07FSummary:
    worlds: dict
    replicates: int
    fit_count: int
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


def run_v07f_replicate(
    *,
    world: str,
    replicate: int,
    seed: int,
    num_warmup: int = 300,
    num_samples: int = 350,
    num_chains: int = 2,
    progress_bar: bool = False,
    target_accept_prob: float = 0.90,
) -> V07FReplicate:
    from esdm.model.backend_numpyro import fit_numpyro

    fixture = build_v07f_fixture()
    generator, theta = generator_for_world(fixture, world)
    generated = simulate_observations(
        generator,
        theta,
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

    return V07FReplicate(
        world=str(world),
        replicate=int(replicate),
        dynamic_heldout_log_score=dynamic_score,
        static_heldout_log_score=static_score,
        dynamic_divergences=dynamic_fit.num_divergences,
        static_divergences=static_fit.num_divergences,
    )


def _summarize_world(world: str, rows) -> V07FWorldSummary:
    selected = tuple(row for row in rows if row.world == world)
    if not selected:
        raise ValueError(f"v0.7f world {world!r} has no records")
    gains = tuple(row.correct_gain for row in selected)
    return V07FWorldSummary(
        world=world,
        replicates=len(selected),
        fit_count=2 * len(selected),
        correct_better_rate=sum(gain > 0.0 for gain in gains) / len(selected),
        mean_correct_gain=math.fsum(gains) / len(selected),
        minimum_correct_gain=min(gains),
        total_divergences=sum(
            int(row.dynamic_divergences) + int(row.static_divergences)
            for row in selected
        ),
    )


def summarize_v07f(records: Sequence[V07FReplicate]) -> V07FSummary:
    rows = tuple(records)
    if not rows:
        raise ValueError("v0.7f records must be non-empty")
    worlds = {
        world: _summarize_world(world, rows)
        for world in V07F_WORLDS
    }
    return V07FSummary(
        worlds=worlds,
        replicates=len(rows),
        fit_count=2 * len(rows),
        total_divergences=sum(
            int(row.dynamic_divergences) + int(row.static_divergences)
            for row in rows
        ),
    )
