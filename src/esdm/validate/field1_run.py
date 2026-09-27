"""Frozen execution plan for FIELD1 known-truth replicates."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from esdm.simulate import simulate_presence_only
from .evidence import poisson_log_predictive_density
from .field1_known_truth import (
    field1_truth_theta,
    make_field1_fixture,
    make_field1_mean_covariance_factorial,
    make_field1_model,
    make_field1_primary_worlds,
    subset_presence_data,
)


@dataclass(frozen=True, slots=True)
class Field1MCMCProfile:
    num_warmup: int = 300
    num_samples: int = 350
    num_chains: int = 2
    target_accept_prob: float = 0.90


FROZEN_FIELD1_MCMC_PROFILE = Field1MCMCProfile()


@dataclass(frozen=True, slots=True)
class Field1ReplicateResult:
    world_id: str
    replicate: int
    gains: Mapping[tuple[str, str, str], float]
    divergences: Mapping[tuple[str, str], int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "gains",
            MappingProxyType(
                {
                    (str(candidate), str(reference), str(holdout)): float(value)
                    for (candidate, reference, holdout), value
                    in dict(self.gains).items()
                }
            ),
        )
        object.__setattr__(
            self,
            "divergences",
            MappingProxyType(
                {
                    (str(holdout), str(model_id)): int(value)
                    for (holdout, model_id), value
                    in dict(self.divergences).items()
                }
            ),
        )


def _worlds():
    rows = (
        *make_field1_primary_worlds(),
        *make_field1_mean_covariance_factorial(),
    )
    return {world.world_id: world for world in rows}


def field1_required_fit_plan(world_id: str):
    """Return unique (holdout, model) fits needed by the frozen comparisons."""

    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown FIELD1 world {world_id!r}")
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


def run_field1_replicate(
    world_id: str,
    replicate: int,
    *,
    base_seed: int = 20260927,
    profile: Field1MCMCProfile = FROZEN_FIELD1_MCMC_PROFILE,
    fit_fn=None,
) -> Field1ReplicateResult:
    """Generate once, fit the finite plan, and score frozen H1/H2 comparisons."""

    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown FIELD1 world {world_id!r}")
    replicate = int(replicate)
    if replicate < 0:
        raise ValueError("FIELD1 replicate must be non-negative")
    world_names = tuple(worlds)
    world_index = world_names.index(name)
    world = worlds[name]
    fixture = make_field1_fixture()

    truth_model = make_field1_model(fixture, world.truth_model_id)
    generation_seed = (
        int(base_seed)
        + world_index * 1_000_000
        + replicate * 10_000
    )
    latent_field_seed = generation_seed + 503
    truth_theta = field1_truth_theta(
        fixture,
        world.truth_model_id,
        mean_environment_beta=world.mean_environment_beta,
        innovation_seed=latent_field_seed,
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

    scores = {}
    divergences = {}
    plan = field1_required_fit_plan(name)
    for fit_index, (holdout, model_id) in enumerate(plan):
        training_spaces = fixture.training_spaces(holdout)
        heldout_spaces = fixture.heldout_spaces(holdout)
        train_model = make_field1_model(
            fixture,
            model_id,
            domain_spaces=training_spaces,
        )
        heldout_model = make_field1_model(
            fixture,
            model_id,
            domain_spaces=heldout_spaces,
        )
        train_data = subset_presence_data(generated.counts, train_model)
        heldout_data = subset_presence_data(generated.counts, heldout_model)

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
        scores[(holdout, model_id)] = poisson_log_predictive_density(
            heldout_model,
            fit.samples,
            fixture.covariates,
            heldout_data,
            stream_name="records",
            species="sp",
        )
        divergences[(holdout, model_id)] = int(fit.num_divergences)

    gains = {}
    for candidate, reference, holdout in (
        *world.expected_positive_comparisons,
        *world.expected_null_comparisons,
    ):
        gains[(candidate, reference, holdout)] = (
            scores[(holdout, candidate)]
            - scores[(holdout, reference)]
        )

    return Field1ReplicateResult(
        world_id=name,
        replicate=replicate,
        gains=gains,
        divergences=divergences,
    )
