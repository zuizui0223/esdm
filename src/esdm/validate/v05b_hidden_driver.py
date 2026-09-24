"""Misspecified hidden-common-driver stress world for v0.5b."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math
import statistics

from esdm.model import Model
from esdm.process import LinearSuitability, PartnerIntensityEffect
from .v05a_directed import build_v05a_fixture


V05B_TARGET = "focal.partner_effect.beta_partner"


@dataclass(frozen=True, slots=True)
class V05BFixture:
    fitting_model: Model
    generating_model: Model
    fitting_covariates: dict
    generating_covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    theta_obs: dict

    def __post_init__(self) -> None:
        for name in ("fitting_covariates", "generating_covariates"):
            object.__setattr__(
                self,
                name,
                MappingProxyType({
                    key: MappingProxyType(dict(values))
                    for key, values in getattr(self, name).items()
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
        object.__setattr__(
            self,
            "theta_obs",
            MappingProxyType({
                name: MappingProxyType(dict(values))
                for name, values in self.theta_obs.items()
            }),
        )


def _hidden_shared_values(base_fixture):
    ordered = tuple(base_fixture.model.domain.keys)
    train = set(base_fixture.train_spaces)
    raw = {}
    for index, key in enumerate(ordered):
        source_driver = float(base_fixture.covariates[key]["source_driver"])
        extra = (
            0.65 * math.sin(2.0 * math.pi * index / 13.0)
            - 0.30 * math.cos(2.0 * math.pi * index / 5.0)
        )
        raw[key] = 0.80 * source_driver + extra

    train_values = tuple(
        raw[key] for key in ordered if key[0] in train
    )
    mean = statistics.fmean(train_values)
    sd = statistics.pstdev(train_values)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("hidden driver requires positive training variation")
    return {
        key: (raw[key] - mean) / sd
        for key in ordered
    }


def build_v05b_fixture() -> V05BFixture:
    base = build_v05a_fixture()
    hidden = _hidden_shared_values(base)
    generating_covariates = {
        key: dict(base.covariates[key], hidden_shared=float(hidden[key]))
        for key in base.model.domain.keys
    }

    source = LinearSuitability(
        covariates=("source_driver", "shared_env", "hidden_shared"),
        intercept_parameter="source_intercept",
        coefficient_parameters={
            "source_driver": "beta_source_driver",
            "shared_env": "beta_source_shared",
            "hidden_shared": "beta_source_hidden",
        },
    )
    focal = LinearSuitability(
        covariates=("focal_driver", "shared_env", "hidden_shared"),
        intercept_parameter="focal_intercept",
        coefficient_parameters={
            "focal_driver": "beta_focal_driver",
            "shared_env": "beta_focal_shared",
            "hidden_shared": "beta_focal_hidden",
        },
    )
    partner = PartnerIntensityEffect(
        source_species="source",
        coefficient_parameter="beta_partner",
        name="partner_effect",
    )
    generating_model = Model(
        domain=base.model.domain,
        species={
            "focal": (focal, partner),
            "source": (source,),
        },
        streams=base.model.streams,
    )
    generating_model.check_design()

    generating_theta = {
        "source": {
            "source_intercept": 0.40,
            "beta_source_driver": 0.55,
            "beta_source_shared": 0.55,
            "beta_source_hidden": 0.90,
        },
        "focal": {
            "focal_intercept": -0.10,
            "beta_focal_driver": 0.65,
            "beta_focal_shared": 0.60,
            "beta_focal_hidden": 0.90,
            "beta_partner": 0.0,
        },
    }

    return V05BFixture(
        fitting_model=base.model,
        generating_model=generating_model,
        fitting_covariates={
            key: dict(values) for key, values in base.covariates.items()
        },
        generating_covariates=generating_covariates,
        train_spaces=base.train_spaces,
        heldout_spaces=base.heldout_spaces,
        generating_theta=generating_theta,
        theta_obs={
            name: dict(values) for name, values in base.theta_obs.items()
        },
    )
