"""Budget-matched direct-occupancy placement fixture for v0.7g."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07b_fixture import (
    V07B_DIRECT_EFFORT,
    V07B_JOINT_TRAIN_COUNT,
    V07B_TRUTH,
    build_v07b_fixture,
)


V07G_CALIBRATION_COUNT = 4
V07G_TOTAL_DIRECT_EFFORT = V07G_CALIBRATION_COUNT * V07B_DIRECT_EFFORT
V07G_BASELINE_PLACEMENT = (1, 2, 3, 4)
V07G_SELECTED_PLACEMENT = (2, 6, 7, 8)
V07G_DYNAMIC_TARGETS = (
    "sp.occupancy.psi0_logit",
    "sp.occupancy.gamma_logit",
    "sp.occupancy.epsilon_logit",
)


@dataclass(frozen=True, slots=True)
class V07GFixture:
    source: object
    training_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    placement: tuple[int, ...]
    total_direct_effort: float


def build_v07g_fixture(placement) -> V07GFixture:
    source = build_v07b_fixture()
    days = tuple(sorted(int(day) for day in placement))
    if len(days) != V07G_CALIBRATION_COUNT or len(set(days)) != len(days):
        raise ValueError(
            f"v0.7g placement must contain exactly {V07G_CALIBRATION_COUNT} unique days"
        )
    valid = set(range(1, V07B_JOINT_TRAIN_COUNT + 1))
    if not set(days).issubset(valid):
        raise ValueError("v0.7g placement must remain inside joint training contexts 1-8")

    direct_effort = {
        key: float(V07B_DIRECT_EFFORT)
        for key in source.training_model.domain.keys
        if int(key[1]) in set(days)
    }
    direct = OccupancyCount(
        "occupancy_calibration",
        effort=EffortField(direct_effort),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )
    joint = next(
        stream
        for stream in source.training_model.streams
        if stream.name == "joint"
    )
    model = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint, direct),
    )
    model.check_design()

    total_effort = sum(float(value) for value in direct_effort.values())
    if total_effort != float(V07G_TOTAL_DIRECT_EFFORT):
        raise RuntimeError("v0.7g direct effort budget drifted")

    return V07GFixture(
        source=source,
        training_model=model,
        covariates=source.covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs=source.generating_theta_obs,
        placement=days,
        total_direct_effort=total_effort,
    )


@dataclass(frozen=True, slots=True)
class V07GValidationFixture:
    source: object
    generator_model: Model
    optimized_model: Model
    baseline_model: Model
    scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    optimized_keys: tuple
    baseline_keys: tuple
    heldout_keys: tuple


def build_v07g_validation_fixture() -> V07GValidationFixture:
    source = build_v07b_fixture()
    all_training_days = set(range(1, V07B_JOINT_TRAIN_COUNT + 1))
    direct = OccupancyCount(
        "occupancy_calibration",
        effort=EffortField({
            key: float(V07B_DIRECT_EFFORT)
            for key in source.generator_model.domain.keys
            if int(key[1]) in all_training_days
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )
    joint_generator = next(
        stream
        for stream in source.generator_model.streams
        if stream.name == "joint"
    )
    generator = Model(
        source.generator_model.domain,
        source.generator_model.species,
        (joint_generator, direct),
    )
    generator.check_design()

    optimized = build_v07g_fixture(V07G_SELECTED_PLACEMENT)
    baseline = build_v07g_fixture(V07G_BASELINE_PLACEMENT)
    if optimized.total_direct_effort != baseline.total_direct_effort:
        raise RuntimeError("v0.7g candidate effort budgets do not match")

    optimized_keys = tuple(
        key
        for key in source.training_model.domain.keys
        if int(key[1]) in set(V07G_SELECTED_PLACEMENT)
    )
    baseline_keys = tuple(
        key
        for key in source.training_model.domain.keys
        if int(key[1]) in set(V07G_BASELINE_PLACEMENT)
    )

    return V07GValidationFixture(
        source=source,
        generator_model=generator,
        optimized_model=optimized.training_model,
        baseline_model=baseline.training_model,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=source.generating_theta,
        generating_theta_obs=source.generating_theta_obs,
        optimized_keys=optimized_keys,
        baseline_keys=baseline_keys,
        heldout_keys=source.heldout_keys,
    )
