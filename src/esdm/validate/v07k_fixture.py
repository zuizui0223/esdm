"""Shift-local burned-pilot fixtures for v0.7k."""

from __future__ import annotations

from dataclasses import dataclass

from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07b_fixture import V07B_DIRECT_EFFORT, build_v07b_fixture
from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_fixture import build_v07i_pilot_fixture
from .v07j_confirm import V07J_WORLDS, theta_for_v07j_world


V07K_WORLDS = V07J_WORLDS
V07K_TRANSFERRED_PLACEMENT = V07G_SELECTED_PLACEMENT
V07K_DIRECT_EFFORT_PER_CONTEXT = float(V07B_DIRECT_EFFORT)
V07K_TOTAL_DIRECT_EFFORT = 4 * V07K_DIRECT_EFFORT_PER_CONTEXT
V07K_ORACLE_PLACEMENTS = {
    "transfer_positive": (1, 3, 7, 8),
    "reversal": (1, 2, 7, 8),
}


def _direct_stream(name, domain, placement):
    days = set(int(day) for day in placement)
    return OccupancyCount(
        str(name),
        effort=EffortField({
            key: V07K_DIRECT_EFFORT_PER_CONTEXT
            for key in domain.keys
            if int(key[1]) in days
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )


@dataclass(frozen=True, slots=True)
class V07KLocalPilotFixture:
    source: object
    generator_model: Model
    training_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    pilot_keys: tuple
    world: str


def build_v07k_local_pilot_fixture(world: str) -> V07KLocalPilotFixture:
    name = str(world)
    if name not in V07K_WORLDS:
        raise KeyError(f"unknown v0.7k world {name!r}")
    source = build_v07i_pilot_fixture()
    return V07KLocalPilotFixture(
        source=source,
        generator_model=source.generator_model,
        training_model=source.training_model,
        covariates=source.covariates,
        generating_theta=theta_for_v07j_world(name),
        generating_theta_obs=source.generating_theta_obs,
        pilot_keys=source.pilot_keys,
        world=name,
    )


@dataclass(frozen=True, slots=True)
class V07KConfirmFixture:
    source: object
    generator_model: Model
    adaptive_model: Model
    transferred_model: Model
    scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    adaptive_placement: tuple[int, ...]
    adaptive_keys: tuple
    transferred_keys: tuple
    heldout_keys: tuple
    world: str


def build_v07k_confirm_fixture(
    world: str,
    adaptive_placement,
) -> V07KConfirmFixture:
    name = str(world)
    if name not in V07K_WORLDS:
        raise KeyError(f"unknown v0.7k world {name!r}")
    placement = tuple(sorted(int(day) for day in adaptive_placement))
    if len(placement) != 4 or len(set(placement)) != 4:
        raise ValueError("v0.7k adaptive placement must contain four unique days")
    if not set(placement).issubset(set(range(1, 9))):
        raise ValueError("v0.7k adaptive placement must remain inside contexts 1-8")

    source = build_v07b_fixture()
    joint_generator = next(
        stream
        for stream in source.generator_model.streams
        if stream.name == "joint"
    )
    joint_training = next(
        stream
        for stream in source.training_model.streams
        if stream.name == "joint"
    )
    adaptive_direct = _direct_stream(
        "adaptive_calibration",
        source.generator_model.domain,
        placement,
    )
    transferred_direct = _direct_stream(
        "transferred_calibration",
        source.generator_model.domain,
        V07K_TRANSFERRED_PLACEMENT,
    )
    generator = Model(
        source.generator_model.domain,
        source.generator_model.species,
        (joint_generator, adaptive_direct, transferred_direct),
    )
    adaptive = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint_training, adaptive_direct),
    )
    transferred = Model(
        source.training_model.domain,
        source.training_model.species,
        (joint_training, transferred_direct),
    )
    for model in (generator, adaptive, transferred):
        model.check_design()

    adaptive_keys = tuple(
        key
        for key in source.training_model.domain.keys
        if int(key[1]) in set(placement)
    )
    transferred_keys = tuple(
        key
        for key in source.training_model.domain.keys
        if int(key[1]) in set(V07K_TRANSFERRED_PLACEMENT)
    )
    return V07KConfirmFixture(
        source=source,
        generator_model=generator,
        adaptive_model=adaptive,
        transferred_model=transferred,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=theta_for_v07j_world(name),
        generating_theta_obs={
            "joint": {},
            "adaptive_calibration": {},
            "transferred_calibration": {},
        },
        adaptive_placement=placement,
        adaptive_keys=adaptive_keys,
        transferred_keys=transferred_keys,
        heldout_keys=source.heldout_keys,
        world=name,
    )
