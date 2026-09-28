"""Frozen-execution primitives for AMAP1 replicates."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from esdm.simulate import simulate_presence_only
from .amap1_known_truth import (
    amap1_truth_theta,
    make_amap1_fixtures,
    make_amap1_model,
    make_amap1_worlds,
    subset_amap1_data,
)
from .evidence import poisson_log_predictive_density


@dataclass(frozen=True, slots=True)
class AMap1MCMCProfile:
    num_warmup: int = 300
    num_samples: int = 350
    num_chains: int = 2
    target_accept_prob: float = 0.90


FROZEN_AMAP1_MCMC_PROFILE = AMap1MCMCProfile()


@dataclass(frozen=True, slots=True)
class AMap1ReplicateResult:
    world_id: str
    replicate: int
    regret: float
    detectability_gain: float | None
    divergences: object

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "divergences",
            MappingProxyType(
                {
                    str(model_id): int(value)
                    for model_id, value in dict(self.divergences).items()
                }
            ),
        )


def _worlds():
    return {world.world_id: world for world in make_amap1_worlds()}


def _fixtures():
    return {
        fixture.geometry_id: fixture
        for fixture in make_amap1_fixtures()
    }


def amap1_required_fit_plan(world_id: str):
    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown AMAP1 world {world_id!r}")
    world = worlds[name]

    required = {"BA", world.oracle_model_id}
    if world.detectability_reference is not None:
        required.add("B0")
    return tuple(sorted(required))


def _fit_seed(
    base_seed: int,
    world_index: int,
    replicate: int,
    fit_index: int,
):
    return (
        int(base_seed)
        + int(world_index) * 1_000_000
        + int(replicate) * 10_000
        + int(fit_index) * 41
        + 1
    )


def run_amap1_replicate(
    world_id: str,
    replicate: int,
    *,
    base_seed: int = 20260928,
    profile: AMap1MCMCProfile = FROZEN_AMAP1_MCMC_PROFILE,
    fit_fn=None,
) -> AMap1ReplicateResult:
    worlds = _worlds()
    name = str(world_id)
    if name not in worlds:
        raise KeyError(f"unknown AMAP1 world {world_id!r}")
    replicate = int(replicate)
    if replicate < 0:
        raise ValueError("AMAP1 replicate must be non-negative")

    world_names = tuple(worlds)
    world_index = world_names.index(name)
    world = worlds[name]
    fixture = _fixtures()[world.geometry_id]

    generation_seed = (
        int(base_seed)
        + world_index * 1_000_000
        + replicate * 10_000
    )
    truth_model = make_amap1_model(fixture, world.truth_model_id)
    truth_theta = amap1_truth_theta(
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

    scores = {}
    divergences = {}
    plan = amap1_required_fit_plan(name)

    for fit_index, model_id in enumerate(plan):
        train_model = make_amap1_model(
            fixture,
            model_id,
            domain_spaces=fixture.training_spaces,
        )
        heldout_model = make_amap1_model(
            fixture,
            model_id,
            domain_spaces=fixture.heldout_spaces,
        )
        train_data = subset_amap1_data(generated.counts, train_model)
        heldout_data = subset_amap1_data(generated.counts, heldout_model)

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
        scores[model_id] = poisson_log_predictive_density(
            heldout_model,
            fit.samples,
            fixture.covariates,
            heldout_data,
            stream_name="records",
            species="sp",
        )
        divergences[model_id] = int(fit.num_divergences)

    regret = scores[world.oracle_model_id] - scores["BA"]
    detectability_gain = None
    if world.detectability_reference is not None:
        candidate, reference = world.detectability_reference
        if candidate != world.oracle_model_id or reference != "B0":
            raise RuntimeError("AMAP1 detectability contract drift")
        detectability_gain = scores[candidate] - scores[reference]

    return AMap1ReplicateResult(
        world_id=name,
        replicate=replicate,
        regret=regret,
        detectability_gain=detectability_gain,
        divergences=divergences,
    )
