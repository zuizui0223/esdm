"""Fresh two-species known-truth worlds for v0.5a directed interaction."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability, PartnerIntensityEffect


V05A_WORLDS = ("interaction", "measured_shared_null")
V05A_TARGET = "focal.partner_effect.beta_partner"


@dataclass(frozen=True, slots=True)
class V05AFixture:
    model: Model
    covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    theta_by_world: dict
    theta_obs: dict

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
            "theta_by_world",
            MappingProxyType({
                world: MappingProxyType({
                    species: MappingProxyType(dict(values))
                    for species, values in theta.items()
                })
                for world, theta in self.theta_by_world.items()
            }),
        )
        object.__setattr__(
            self,
            "theta_obs",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.theta_obs.items()
            }),
        )


def _covariate_rows(n: int = 36):
    rows = []
    for index in range(n):
        shared = ((index % 12) - 5.5) / 3.5
        source_driver = (
            math.sin(2.0 * math.pi * index / 9.0)
            + 0.35 * math.cos(2.0 * math.pi * index / 5.0)
        )
        focal_driver = (
            math.cos(2.0 * math.pi * index / 7.0)
            - 0.25 * math.sin(2.0 * math.pi * index / 4.0)
        )
        rows.append(
            {
                "shared_env": float(shared),
                "source_driver": float(source_driver),
                "focal_driver": float(focal_driver),
            }
        )
    return tuple(rows)


def build_v05a_fixture() -> V05AFixture:
    spaces = tuple(f"s{index:02d}" for index in range(36))
    train_spaces = spaces[:24]
    heldout_spaces = spaces[24:]
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    rows = _covariate_rows(len(spaces))
    covariates = {
        key: dict(rows[index])
        for index, key in enumerate(grid.keys)
    }

    source_process = LinearSuitability(
        covariates=("source_driver", "shared_env"),
        intercept_parameter="source_intercept",
        coefficient_parameters={
            "source_driver": "beta_source_driver",
            "shared_env": "beta_source_shared",
        },
    )
    focal_process = LinearSuitability(
        covariates=("focal_driver", "shared_env"),
        intercept_parameter="focal_intercept",
        coefficient_parameters={
            "focal_driver": "beta_focal_driver",
            "shared_env": "beta_focal_shared",
        },
    )
    partner = PartnerIntensityEffect(
        source_species="source",
        coefficient_parameter="beta_partner",
        name="partner_effect",
    )
    effort = {key: 6.0 for key in grid.keys}
    model = Model(
        domain=grid,
        species={
            "focal": (focal_process, partner),
            "source": (source_process,),
        },
        streams=(
            PresenceOnly(
                "source_records",
                effort=EffortField(effort),
                informs=frozenset({"suitability"}),
                targets=frozenset({"source"}),
            ),
            PresenceOnly(
                "focal_records",
                effort=EffortField(effort),
                informs=frozenset({"suitability", "partner_effect"}),
                targets=frozenset({"focal"}),
            ),
        ),
    )
    model.check_design()

    shared_source = {
        "source_intercept": 0.40,
        "beta_source_driver": 0.90,
        "beta_source_shared": 0.55,
    }
    shared_focal = {
        "focal_intercept": -0.10,
        "beta_focal_driver": 0.65,
        "beta_focal_shared": 0.60,
    }
    theta_by_world = {
        "interaction": {
            "source": dict(shared_source),
            "focal": dict(shared_focal, beta_partner=0.75),
        },
        "measured_shared_null": {
            "source": dict(shared_source),
            "focal": dict(shared_focal, beta_partner=0.0),
        },
    }
    return V05AFixture(
        model=model,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        theta_by_world=theta_by_world,
        theta_obs={"source_records": {}, "focal_records": {}},
    )


def v05a_theta(fixture: V05AFixture, world: str):
    name = str(world)
    if name not in V05A_WORLDS:
        raise ValueError("unknown v0.5a world")
    return {
        species: dict(values)
        for species, values in fixture.theta_by_world[name].items()
    }
