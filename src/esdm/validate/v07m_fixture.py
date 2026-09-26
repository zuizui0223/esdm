"""Fresh disjoint fixtures for v0.7m three-way calibration policy."""
from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount
from .v07b_fixture import V07B_DIRECT_EFFORT, build_v07b_fixture
from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_fixture import build_v07i_pilot_fixture
from .v07m_policy import V07M_EXPECTED_ACTIONS, V07M_ROLE_CELL_IDS


V07M_WORLDS = tuple(V07M_ROLE_CELL_IDS)
V07M_WORLD_PROBABILITIES = {
    "adaptive_large_headroom": {
        "alpha": 0.30,
        "psi0": 0.85,
        "gamma": 0.45,
        "epsilon": 0.38,
    },
    "adaptive_absolute_rescue": {
        "alpha": 0.30,
        "psi0": 0.35,
        "gamma": 0.25,
        "epsilon": 0.22,
    },
    "transfer_adequate": {
        "alpha": 0.30,
        "psi0": 0.35,
        "gamma": 0.25,
        "epsilon": 0.08,
    },
    "abstain_inadequate": {
        "alpha": 0.30,
        "psi0": 0.65,
        "gamma": 0.45,
        "epsilon": 0.08,
    },
}
V07M_ORACLE_PLACEMENTS = {
    "adaptive_large_headroom": (1, 2, 7, 8),
    "adaptive_absolute_rescue": (1, 2, 7, 8),
    "transfer_adequate": (1, 3, 7, 8),
    "abstain_inadequate": (1, 2, 3, 8),
}
V07M_TRANSFERRED_PLACEMENT = V07G_SELECTED_PLACEMENT
V07M_DIRECT_EFFORT_PER_CONTEXT = float(V07B_DIRECT_EFFORT)


def _logit(probability: float) -> float:
    p = float(probability)
    if not 0.0 < p < 1.0:
        raise ValueError("v0.7m probabilities must lie strictly between zero and one")
    return math.log(p / (1.0 - p))


def theta_for_v07m_world(world: str) -> dict:
    name = str(world)
    if name not in V07M_WORLD_PROBABILITIES:
        raise KeyError(f"unknown v0.7m world {name!r}")
    truth = V07M_WORLD_PROBABILITIES[name]
    return {
        "sp": {
            "alpha": float(truth["alpha"]),
            "psi0_logit": _logit(float(truth["psi0"])),
            "gamma_logit": _logit(float(truth["gamma"])),
            "epsilon_logit": _logit(float(truth["epsilon"])),
        }
    }


def truth_sites_for_v07m_world(world: str) -> dict[str, float]:
    theta = theta_for_v07m_world(world)["sp"]
    return {
        "sp.suitability.alpha": float(theta["alpha"]),
        "sp.occupancy.psi0_logit": float(theta["psi0_logit"]),
        "sp.occupancy.gamma_logit": float(theta["gamma_logit"]),
        "sp.occupancy.epsilon_logit": float(theta["epsilon_logit"]),
    }


def _direct_stream(name, domain, placement):
    days = set(int(day) for day in placement)
    return OccupancyCount(
        str(name),
        effort=EffortField({
            key: V07M_DIRECT_EFFORT_PER_CONTEXT
            for key in domain.keys
            if int(key[1]) in days
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )


@dataclass(frozen=True, slots=True)
class V07MLocalPilotFixture:
    source: object
    generator_model: Model
    training_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    pilot_keys: tuple
    world: str
    expected_action: str


def build_v07m_local_pilot_fixture(world: str) -> V07MLocalPilotFixture:
    name = str(world)
    if name not in V07M_WORLDS:
        raise KeyError(f"unknown v0.7m world {name!r}")
    source = build_v07i_pilot_fixture()
    return V07MLocalPilotFixture(
        source=source,
        generator_model=source.generator_model,
        training_model=source.training_model,
        covariates=source.covariates,
        generating_theta=theta_for_v07m_world(name),
        generating_theta_obs=source.generating_theta_obs,
        pilot_keys=source.pilot_keys,
        world=name,
        expected_action=V07M_EXPECTED_ACTIONS[name],
    )


@dataclass(frozen=True, slots=True)
class V07MConfirmFixture:
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
    expected_action: str


def build_v07m_confirm_fixture(
    world: str,
    adaptive_placement,
) -> V07MConfirmFixture:
    name = str(world)
    if name not in V07M_WORLDS:
        raise KeyError(f"unknown v0.7m world {name!r}")
    placement = tuple(sorted(int(day) for day in adaptive_placement))
    if len(placement) != 4 or len(set(placement)) != 4:
        raise ValueError("v0.7m adaptive placement must contain four unique days")
    if not set(placement).issubset(set(range(1, 9))):
        raise ValueError("v0.7m adaptive placement must remain inside contexts 1-8")

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
        V07M_TRANSFERRED_PLACEMENT,
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
        if int(key[1]) in set(V07M_TRANSFERRED_PLACEMENT)
    )
    return V07MConfirmFixture(
        source=source,
        generator_model=generator,
        adaptive_model=adaptive,
        transferred_model=transferred,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=theta_for_v07m_world(name),
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
        expected_action=V07M_EXPECTED_ACTIONS[name],
    )
