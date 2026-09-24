"""Known-truth directed partner-dependence benchmark for v0.5a."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability, PartnerIntensityEffect
from .v04_r2_state_activity import build_v04_r2_fixture


V05A_WORLDS = ("directed_positive", "interaction_null")
V05A_TARGET = "focal.partner_effect.beta_partner"


@dataclass(frozen=True, slots=True)
class V05AFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: Mapping[str, Mapping[str, float]]
    generating_theta_obs: Mapping[str, Mapping[str, float]]
    world: str

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


def _source_process():
    return LinearSuitability(
        covariates=("precip_z_train", "lat_z_train"),
        intercept_parameter="source_intercept",
        coefficient_parameters={
            "precip_z_train": "source_beta_precip",
            "lat_z_train": "source_beta_lat",
        },
    )


def _focal_processes():
    return (
        LinearSuitability(
            covariates=("precip_z_train", "eastness_z_train"),
            intercept_parameter="focal_intercept",
            coefficient_parameters={
                "precip_z_train": "focal_beta_precip",
                "eastness_z_train": "focal_beta_eastness",
            },
        ),
        PartnerIntensityEffect(
            source_species="source",
            coefficient_parameter="beta_partner",
            name="partner_effect",
        ),
    )


def _stream(name, grid, target, informs):
    return PresenceOnly(
        name=name,
        effort=EffortField({key: 6.0 for key in grid.keys}),
        detection_probability=0.90,
        informs=frozenset(informs),
        targets=frozenset({target}),
    )


def build_v05a_fixture(source_csv_text: str, *, world: str) -> V05AFixture:
    normalized = str(world)
    if normalized not in V05A_WORLDS:
        raise ValueError("unknown v0.5a world")

    r2 = build_v04_r2_fixture(source_csv_text, profile="positive")
    doy = r2.model.domain.doy[0]
    hour = r2.model.domain.hour[0]
    spaces = tuple(r2.model.domain.space)
    grid = Grid(space=spaces, doy=(doy,), hour=(hour,))
    covariates = {
        key: {
            "precip_z_train": float(r2.covariates[key]["precip_z_train"]),
            "lat_z_train": float(r2.covariates[key]["lat_z_train"]),
            "eastness_z_train": float(r2.covariates[key]["eastness_z_train"]),
        }
        for key in grid.keys
    }

    model = Model(
        domain=grid,
        species={
            "focal": _focal_processes(),
            "source": (_source_process(),),
        },
        streams=(
            _stream("source_records", grid, "source", {"suitability"}),
            _stream(
                "focal_records",
                grid,
                "focal",
                {"suitability", "partner_effect"},
            ),
        ),
    )
    model.check_design()

    beta = 0.80 if normalized == "directed_positive" else 0.0
    theta = {
        "source": {
            "source_intercept": 0.15,
            "source_beta_precip": 0.70,
            "source_beta_lat": -0.35,
        },
        "focal": {
            "focal_intercept": -0.10,
            "focal_beta_precip": -0.45,
            "focal_beta_eastness": 0.25,
            "beta_partner": beta,
        },
    }
    return V05AFixture(
        model=model,
        covariates=covariates,
        train_spaces=r2.train_spaces,
        heldout_spaces=r2.heldout_spaces,
        generating_theta=theta,
        generating_theta_obs={
            "source_records": {},
            "focal_records": {},
        },
        world=normalized,
    )


def v05a_beta_truth(world: str) -> float:
    normalized = str(world)
    if normalized == "directed_positive":
        return 0.80
    if normalized == "interaction_null":
        return 0.0
    raise ValueError("unknown v0.5a world")
