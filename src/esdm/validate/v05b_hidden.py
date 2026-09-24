"""Hidden-common-driver misspecification world for v0.5b."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.model import Model
from esdm.process import LinearSuitability, PartnerIntensityEffect
from .v05a_directed import build_v05a_fixture


V05B_TARGET = "focal.partner_effect.beta_partner"


@dataclass(frozen=True, slots=True)
class V05BFixture:
    generating_model: Model
    fitting_model: Model
    generating_covariates: dict
    fitting_covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    theta_obs: dict

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generating_covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.generating_covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "fitting_covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.fitting_covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({
                species: MappingProxyType(dict(values))
                for species, values in self.generating_theta.items()
            }),
        )


def build_v05b_fixture() -> V05BFixture:
    fit = build_v05a_fixture()
    generating_covariates = {}
    for index, key in enumerate(fit.model.domain.keys):
        base = dict(fit.covariates[key])
        hidden = (
            0.75 * base["source_driver"]
            + 0.55 * math.sin(2.0 * math.pi * index / 11.0 + 0.4)
        )
        base["hidden_driver"] = float(hidden)
        generating_covariates[key] = base

    source = LinearSuitability(
        covariates=("source_driver", "shared_env", "hidden_driver"),
        intercept_parameter="source_intercept",
        coefficient_parameters={
            "source_driver": "beta_source_driver",
            "shared_env": "beta_source_shared",
            "hidden_driver": "beta_source_hidden",
        },
    )
    focal = LinearSuitability(
        covariates=("focal_driver", "shared_env", "hidden_driver"),
        intercept_parameter="focal_intercept",
        coefficient_parameters={
            "focal_driver": "beta_focal_driver",
            "shared_env": "beta_focal_shared",
            "hidden_driver": "beta_focal_hidden",
        },
    )
    partner = PartnerIntensityEffect(
        source_species="source",
        coefficient_parameter="beta_partner",
        name="partner_effect",
    )
    generating_model = Model(
        domain=fit.model.domain,
        species={
            "focal": (focal, partner),
            "source": (source,),
        },
        streams=fit.model.streams,
    )
    generating_model.check_design()

    return V05BFixture(
        generating_model=generating_model,
        fitting_model=fit.model,
        generating_covariates=generating_covariates,
        fitting_covariates={
            key: dict(values) for key, values in fit.covariates.items()
        },
        train_spaces=fit.train_spaces,
        heldout_spaces=fit.heldout_spaces,
        generating_theta={
            "source": {
                "source_intercept": 0.40,
                "beta_source_driver": 0.90,
                "beta_source_shared": 0.55,
                "beta_source_hidden": 0.90,
            },
            "focal": {
                "focal_intercept": -0.10,
                "beta_focal_driver": 0.65,
                "beta_focal_shared": 0.60,
                "beta_focal_hidden": 1.00,
                "beta_partner": 0.0,
            },
        },
        theta_obs={"source_records": {}, "focal_records": {}},
    )
