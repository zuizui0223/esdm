"""Matched static-versus-dynamic occupancy benchmark fixture for v0.7c."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from esdm.process import LinearSuitability, StaticLinearOccupancy
from .v07b_fixture import (
    V07B_DIRECT_TRAIN_COUNT,
    V07B_HELDOUT_COUNT,
    V07B_JOINT_TRAIN_COUNT,
    V07B_TIMEPOINTS,
    build_v07b_fixture,
)


V07C_STATIC_NOMINAL = {
    "sp.suitability.alpha": 0.30,
    "sp.occupancy.occupancy_intercept": -0.50,
    "sp.occupancy.beta_time": 1.50,
}


@dataclass(frozen=True, slots=True)
class V07CFixture:
    generator_model: Model
    dynamic_training_model: Model
    static_training_model: Model
    dynamic_scoring_model: Model
    static_scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    static_nominal_theta: dict
    joint_train_keys: tuple
    direct_train_keys: tuple
    heldout_keys: tuple


def _static_processes():
    return (
        LinearSuitability(
            covariates=(),
            intercept_parameter="alpha",
            coefficient_parameters={},
        ),
        StaticLinearOccupancy(
            covariates=("time",),
            intercept_parameter="occupancy_intercept",
            coefficient_parameters={"time": "beta_time"},
        ),
    )


def build_v07c_fixture() -> V07CFixture:
    source = build_v07b_fixture()
    keys = tuple(source.generator_model.domain.keys)

    if len(keys) != V07B_TIMEPOINTS:
        raise RuntimeError("v0.7c requires the frozen v0.7b 12-context domain")
    if len(source.joint_train_keys) != V07B_JOINT_TRAIN_COUNT:
        raise RuntimeError("v0.7c joint training split drifted")
    if len(source.direct_train_keys) != V07B_DIRECT_TRAIN_COUNT:
        raise RuntimeError("v0.7c direct calibration split drifted")
    if len(source.heldout_keys) != V07B_HELDOUT_COUNT:
        raise RuntimeError("v0.7c held-out split drifted")

    denominator = max(1, len(keys) - 1)
    covariates = {}
    for index, key in enumerate(keys):
        covariates[key] = {
            "time": -1.0 + 2.0 * index / denominator,
        }

    training_streams = source.training_model.streams
    scoring_streams = source.scoring_model.streams

    static_training = Model(
        source.training_model.domain,
        {"sp": _static_processes()},
        training_streams,
    )
    static_scoring = Model(
        source.scoring_model.domain,
        {"sp": _static_processes()},
        scoring_streams,
    )
    static_training.check_design()
    static_scoring.check_design()

    static_theta = {
        "sp": {
            "alpha": V07C_STATIC_NOMINAL["sp.suitability.alpha"],
            "occupancy_intercept": V07C_STATIC_NOMINAL[
                "sp.occupancy.occupancy_intercept"
            ],
            "beta_time": V07C_STATIC_NOMINAL["sp.occupancy.beta_time"],
        }
    }

    return V07CFixture(
        generator_model=source.generator_model,
        dynamic_training_model=source.training_model,
        static_training_model=static_training,
        dynamic_scoring_model=source.scoring_model,
        static_scoring_model=static_scoring,
        covariates=covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs=source.generating_theta_obs,
        static_nominal_theta=static_theta,
        joint_train_keys=source.joint_train_keys,
        direct_train_keys=source.direct_train_keys,
        heldout_keys=source.heldout_keys,
    )
