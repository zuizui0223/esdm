"""Out-of-family temporal-resolution robustness fixture for v0.7f."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.model import Model
from esdm.process import (
    ColonizationExtinctionOccupancy,
    LinearSuitability,
    StaticLinearOccupancy,
)
from .v07d_fixture import build_v07d_fixture


V07F_WORLDS = ("dynamic_like", "static_like")

V07F_DYNAMIC_LIKE_TRUTH = {
    "alpha": 0.30,
    "psi0": 0.20,
    "gamma0": 0.30,
    "epsilon0": 0.12,
    "beta_gamma_time": 0.55,
    "beta_epsilon_time": -0.35,
}

V07F_STATIC_LIKE_TRUTH = {
    "alpha": 0.30,
    "occupancy_intercept": -0.50,
    "beta_time": 1.50,
    "beta_time2": 0.25,
    "beta_time3": 0.35,
}


def _logit(probability: float) -> float:
    p = float(probability)
    return math.log(p / (1.0 - p))


@dataclass(frozen=True, slots=True)
class V07FFixture:
    dynamic_generator: Model
    static_generator: Model
    dynamic_training_model: Model
    static_training_model: Model
    dynamic_scoring_model: Model
    static_scoring_model: Model
    covariates: dict
    dynamic_generating_theta: dict
    static_generating_theta: dict
    generating_theta_obs: dict
    joint_train_keys: tuple
    direct_train_keys: tuple
    heldout_keys: tuple


def _suitability():
    return LinearSuitability(
        covariates=(),
        intercept_parameter="alpha",
        coefficient_parameters={},
    )


def _dynamic_like_processes():
    truth = V07F_DYNAMIC_LIKE_TRUTH
    return (
        _suitability(),
        ColonizationExtinctionOccupancy(
            initial_logit_parameter="psi0_logit",
            colonization_intercept_parameter="gamma_logit",
            extinction_intercept_parameter="epsilon_logit",
            colonization_covariates=("time",),
            colonization_coefficient_parameters={
                "time": "beta_gamma_time",
            },
            extinction_covariates=("time",),
            extinction_coefficient_parameters={
                "time": "beta_epsilon_time",
            },
        ),
    )


def _static_like_processes():
    return (
        _suitability(),
        StaticLinearOccupancy(
            covariates=("time", "time2", "time3"),
            intercept_parameter="occupancy_intercept",
            coefficient_parameters={
                "time": "beta_time",
                "time2": "beta_time2",
                "time3": "beta_time3",
            },
        ),
    )


def build_v07f_fixture() -> V07FFixture:
    source = build_v07d_fixture()
    keys = tuple(source.generator_model.domain.keys)

    covariates = {}
    for key in keys:
        base = dict(source.covariates[key])
        time = float(base["time"])
        base["time3"] = time * time * time
        covariates[key] = base

    dynamic_generator = Model(
        source.generator_model.domain,
        {"sp": _dynamic_like_processes()},
        source.generator_model.streams,
    )
    static_generator = Model(
        source.generator_model.domain,
        {"sp": _static_like_processes()},
        source.generator_model.streams,
    )
    dynamic_generator.check_design()
    static_generator.check_design()

    dtruth = V07F_DYNAMIC_LIKE_TRUTH
    dynamic_theta = {
        "sp": {
            "alpha": dtruth["alpha"],
            "psi0_logit": _logit(dtruth["psi0"]),
            "gamma_logit": _logit(dtruth["gamma0"]),
            "epsilon_logit": _logit(dtruth["epsilon0"]),
            "beta_gamma_time": dtruth["beta_gamma_time"],
            "beta_epsilon_time": dtruth["beta_epsilon_time"],
        }
    }

    struth = V07F_STATIC_LIKE_TRUTH
    static_theta = {
        "sp": {
            "alpha": struth["alpha"],
            "occupancy_intercept": struth["occupancy_intercept"],
            "beta_time": struth["beta_time"],
            "beta_time2": struth["beta_time2"],
            "beta_time3": struth["beta_time3"],
        }
    }

    return V07FFixture(
        dynamic_generator=dynamic_generator,
        static_generator=static_generator,
        dynamic_training_model=source.dynamic_training_model,
        static_training_model=source.static_training_model,
        dynamic_scoring_model=source.dynamic_scoring_model,
        static_scoring_model=source.static_scoring_model,
        covariates=covariates,
        dynamic_generating_theta=dynamic_theta,
        static_generating_theta=static_theta,
        generating_theta_obs=source.generating_theta_obs,
        joint_train_keys=source.joint_train_keys,
        direct_train_keys=source.direct_train_keys,
        heldout_keys=source.heldout_keys,
    )


def generator_for_world(fixture: V07FFixture, world: str):
    name = str(world)
    if name == "dynamic_like":
        return fixture.dynamic_generator, fixture.dynamic_generating_theta
    if name == "static_like":
        return fixture.static_generator, fixture.static_generating_theta
    raise KeyError(f"unknown v0.7f world {name!r}")
