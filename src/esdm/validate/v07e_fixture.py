"""Reciprocal static-world specificity fixture for v0.7e."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from .v07d_fixture import build_v07d_fixture


@dataclass(frozen=True, slots=True)
class V07EFixture:
    generator_model: Model
    dynamic_training_model: Model
    static_training_model: Model
    dynamic_scoring_model: Model
    static_scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    joint_train_keys: tuple
    direct_train_keys: tuple
    heldout_keys: tuple


def build_v07e_fixture() -> V07EFixture:
    source = build_v07d_fixture()
    static_processes = source.static_training_model.species["sp"]

    generator = Model(
        source.generator_model.domain,
        {"sp": static_processes},
        source.generator_model.streams,
    )
    generator.check_design()

    dynamic_count = sum(
        len(process.priors())
        for process in source.dynamic_training_model.species["sp"]
    )
    static_count = sum(
        len(process.priors())
        for process in source.static_training_model.species["sp"]
    )
    if dynamic_count != 4 or static_count != 4:
        raise RuntimeError("v0.7e requires the frozen equal-dimension 4-vs-4 models")

    return V07EFixture(
        generator_model=generator,
        dynamic_training_model=source.dynamic_training_model,
        static_training_model=source.static_training_model,
        dynamic_scoring_model=source.dynamic_scoring_model,
        static_scoring_model=source.static_scoring_model,
        covariates=source.covariates,
        generating_theta=source.static_nominal_theta,
        generating_theta_obs=source.generating_theta_obs,
        joint_train_keys=source.joint_train_keys,
        direct_train_keys=source.direct_train_keys,
        heldout_keys=source.heldout_keys,
    )
