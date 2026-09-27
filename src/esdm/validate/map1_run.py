"""Frozen execution plan for MAP1 known-truth replicates."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from esdm.simulate import simulate_presence_only
from .evidence import poisson_log_predictive_density
from .map1_known_truth import (
    make_map1_fixture,
    make_map1_model,
    make_map1_worlds,
    map1_truth_theta,
    subset_map1_data,
)


@dataclass(frozen=True, slots=True)
class Map1MCMCProfile:
    num_warmup: int = 300
    num_samples: int = 350
    num_chains: int = 2
    target_accept_prob: float = 0.90


FROZEN_MAP1_MCMC_PROFILE = Map1MCMCProfile()


@dataclass(frozen=True, slots=True)
class Map1ReplicateResult:
    world_id: str
    replicate: int
    gains: object
    divergences: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "gains",
            MappingProxyType(
                {
                    (str(candidate), str(reference), str(holdout)): float(value)
                    for (candidate, reference, holdout), value in dict(self.gains).items()
                }
            ),
        )
        object.__setattr__(
            self,
            "divergences",
            MappingProxyType(
                {
                    (str(holdout), str(model_id)): int(value)
                    for (holdout, model_id), value in dict(self.divergences).items()
                }
            ),
        )


def _worlds():
    return {world.world_id: world for world in make_map1_worlds()}


def map1_required_fit_plan(world_id: str):
    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown MAP1 world {world_id!r}")
    world = worlds[name]
    required = set()
    for candidate, reference, holdout in (
        *world.expected_positive_comparisons,
        *world.expected_null_comparisons,
    ):
        required.add((str(holdout), str(candidate)))
        required.add((str(holdout), str(reference)))
    return tuple(sorted(required))


def _fit_seed(base_seed: int, world_index: int, replicate: int, fit_index: int):
    return (
        int(base_seed)
        + int(world_index) * 1_000_000
        + int(replicate) * 10_000
        + int(fit_index) * 37
        + 1
    )


def run_map1_replicate(
    world_id: str,
    replicate: int,
    *,
    base_seed: int = 20260927,
    profile: Map1MCMCProfile = FROZEN_MAP1_MCMC_PROFILE,
    fit_fn=None,
) -> Map1ReplicateResult:
    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown MAP1 world {world_id!r}")
    replicate = int(replicate)
    if replicate < 0:
        raise ValueError("MAP1 replicate must be non-negative")

    world_names = tuple(worlds)
    world_index = world_names.index(name)
    world = worlds[name]
    fixture = make_map1_fixture()

    generation_seed = (
        int(base_seed)
        + world_index * 1_000_000
        + replicate * 10_000
    )
    truth_model = make_map1_model(fixture, world.truth_model_id)
    truth_theta = map1_truth_theta(
        fixture,
        world.truth_model_id,
        innovation_seed=generation_seed + 503,
    )
    generated = simulate_presence_only(
        truth_model,
        truth_theta,
        fixture.covariates,
        seed=generation_seed,
    )

    if fit_fn is None:
        from esdm.model.backend_numpyro import fit_numpyro
        fit_fn = fit_numpyro

    training = fixture.training_spaces()
    heldout = fixture.heldout_spaces()
    scores = {}
    divergences = {}
    plan = map1_required_fit_plan(name)

    for fit_index, (holdout_name, model_id) in enumerate(plan):
        if holdout_name != "H1":
            raise RuntimeError(f"undeclared MAP1 holdout {holdout_name!r}")
        train_model = make_map1_model(
            fixture,
            model_id,
            domain_spaces=training,
        )
        heldout_model = make_map1_model(
            fixture,
            model_id,
            domain_spaces=heldout,
        )
        train_data = subset_map1_data(generated.counts, train_model)
        heldout_data = subset_map1_data(generated.counts, heldout_model)

        fit = fit_fn(
            train_model,
            train_data,
            fixture.covariates,
            rng_seed=_fit_seed(
                base_seed,
                world_index,
                replicate,
                fit_index,
            ),
            num_warmup=int(profile.num_warmup),
            num_samples=int(profile.num_samples),
            num_chains=int(profile.num_chains),
            progress_bar=False,
            target_accept_prob=float(profile.target_accept_prob),
        )
        scores[(holdout_name, model_id)] = poisson_log_predictive_density(
            heldout_model,
            fit.samples,
            fixture.covariates,
            heldout_data,
            stream_name="records",
            species="sp",
        )
        divergences[(holdout_name, model_id)] = int(fit.num_divergences)

    gains = {}
    for candidate, reference, holdout_name in (
        *world.expected_positive_comparisons,
        *world.expected_null_comparisons,
    ):
        gains[(candidate, reference, holdout_name)] = (
            scores[(holdout_name, candidate)]
            - scores[(holdout_name, reference)]
        )

    return Map1ReplicateResult(
        world_id=name,
        replicate=replicate,
        gains=gains,
        divergences=divergences,
    )
