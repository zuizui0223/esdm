"""Source-only perturbation qualification design for v0.5b."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from esdm.model import Model
from esdm.process import LinearSuitability
from .v05a_directed import V05A_WORLDS, V05A_TARGET, build_v05a_fixture


V05B_PERTURBATION_BETA = 1.0


@dataclass(frozen=True, slots=True)
class V05BFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: Mapping[str, Mapping[str, float]]
    generating_theta_obs: Mapping[str, Mapping[str, float]]
    world: str
    perturbation_by_space: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.generating_theta.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.generating_theta_obs.items()
            }),
        )
        object.__setattr__(
            self,
            "perturbation_by_space",
            MappingProxyType({
                str(space): float(value)
                for space, value in self.perturbation_by_space.items()
            }),
        )


def _source_perturbation_assignment(base) -> dict[str, float]:
    doy = base.model.domain.doy[0]
    hour = base.model.domain.hour[0]
    ordered = sorted(
        base.train_spaces,
        key=lambda space: (
            float(base.covariates[(space, doy, hour)]["eastness_z_train"]),
            float(base.covariates[(space, doy, hour)]["precip_z_train"]),
            str(space),
        ),
    )
    permutations = (
        (-1.0, 0.0, 1.0),
        (0.0, 1.0, -1.0),
        (1.0, -1.0, 0.0),
    )
    assignment: dict[str, float] = {}
    for index, space in enumerate(ordered):
        block = index // 3
        within = index % 3
        assignment[space] = permutations[block % len(permutations)][within]
    for space in base.heldout_spaces:
        assignment[space] = 0.0
    return assignment


def _perturbed_source_process():
    return LinearSuitability(
        covariates=(
            "precip_z_train",
            "lat_z_train",
            "source_perturbation",
        ),
        intercept_parameter="source_intercept",
        coefficient_parameters={
            "precip_z_train": "source_beta_precip",
            "lat_z_train": "source_beta_lat",
            "source_perturbation": "source_beta_perturbation",
        },
    )


def build_v05b_fixture(source_csv_text: str, *, world: str) -> V05BFixture:
    normalized = str(world)
    if normalized not in V05A_WORLDS:
        raise ValueError("unknown v0.5b world")

    base = build_v05a_fixture(source_csv_text, world=normalized)
    assignment = _source_perturbation_assignment(base)
    covariates = {}
    for key, values in base.covariates.items():
        covariates[key] = {
            **dict(values),
            "source_perturbation": float(assignment[key[0]]),
        }

    model = Model(
        domain=base.model.domain,
        species={
            "focal": base.model.species["focal"],
            "source": (_perturbed_source_process(),),
        },
        streams=base.model.streams,
    )
    model.check_design()

    theta = {
        species: dict(values)
        for species, values in base.generating_theta.items()
    }
    theta["source"]["source_beta_perturbation"] = V05B_PERTURBATION_BETA

    return V05BFixture(
        model=model,
        covariates=covariates,
        train_spaces=base.train_spaces,
        heldout_spaces=base.heldout_spaces,
        generating_theta=theta,
        generating_theta_obs=base.generating_theta_obs,
        world=normalized,
        perturbation_by_space=assignment,
    )
