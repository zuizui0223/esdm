"""Fresh known-truth recovery/transfer fixture for v0.7b dynamic occupancy."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount, OccupiedPresenceOnly
from esdm.process import ColonizationExtinctionOccupancy, LinearSuitability


V07B_TRUTH = {
    "sp.suitability.alpha": 0.30,
    "sp.occupancy.psi0_logit": math.log(0.20 / 0.80),
    "sp.occupancy.gamma_logit": math.log(0.35 / 0.65),
    "sp.occupancy.epsilon_logit": math.log(0.15 / 0.85),
}

V07B_TIMEPOINTS = 12
V07B_JOINT_TRAIN_COUNT = 8
V07B_DIRECT_TRAIN_COUNT = 4
V07B_HELDOUT_COUNT = 4
V07B_JOINT_EFFORT = 500.0
V07B_DIRECT_EFFORT = 500.0


@dataclass(frozen=True, slots=True)
class V07BFixture:
    generator_model: Model
    training_model: Model
    refusal_model: Model
    scoring_model: Model
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    joint_train_keys: tuple
    direct_train_keys: tuple
    heldout_keys: tuple


def _processes():
    return (
        LinearSuitability(
            covariates=(),
            intercept_parameter="alpha",
            coefficient_parameters={},
        ),
        ColonizationExtinctionOccupancy(
            initial_logit_parameter="psi0_logit",
            colonization_intercept_parameter="gamma_logit",
            extinction_intercept_parameter="epsilon_logit",
        ),
    )


def _joint_stream(name, keys, exposed_keys):
    exposed = set(exposed_keys)
    return OccupiedPresenceOnly(
        name,
        effort=EffortField({
            key: V07B_JOINT_EFFORT
            for key in keys
            if key in exposed
        }),
        informs=frozenset({"suitability", "occupancy"}),
        targets=frozenset({"sp"}),
    )


def _direct_stream(keys, exposed_keys):
    exposed = set(exposed_keys)
    return OccupancyCount(
        "occupancy_calibration",
        effort=EffortField({
            key: V07B_DIRECT_EFFORT
            for key in keys
            if key in exposed
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )


def build_v07b_fixture() -> V07BFixture:
    grid = Grid(
        space=("trajectory",),
        doy=tuple(range(1, V07B_TIMEPOINTS + 1)),
        hour=(0,),
    )
    keys = tuple(grid.keys)
    joint_train_keys = keys[:V07B_JOINT_TRAIN_COUNT]
    direct_train_keys = keys[:V07B_DIRECT_TRAIN_COUNT]
    heldout_keys = keys[-V07B_HELDOUT_COUNT:]
    if set(joint_train_keys) & set(heldout_keys):
        raise RuntimeError("v0.7b train and held-out joint contexts must be disjoint")
    if not set(direct_train_keys).issubset(set(joint_train_keys)):
        raise RuntimeError("v0.7b direct calibration must be training-only")

    covariates = {key: {} for key in keys}
    processes = _processes()

    generator_model = Model(
        grid,
        {"sp": processes},
        (
            _joint_stream("joint", keys, keys),
            _direct_stream(keys, direct_train_keys),
        ),
    )
    training_model = Model(
        grid,
        {"sp": processes},
        (
            _joint_stream("joint", keys, joint_train_keys),
            _direct_stream(keys, direct_train_keys),
        ),
    )
    refusal_model = Model(
        grid,
        {"sp": processes},
        (_joint_stream("joint", keys, joint_train_keys),),
    )
    scoring_model = Model(
        grid,
        {"sp": processes},
        (_joint_stream("joint", keys, heldout_keys),),
    )
    for model in (generator_model, training_model, refusal_model, scoring_model):
        model.check_design()

    theta = {
        "sp": {
            "alpha": 0.30,
            "psi0_logit": math.log(0.20 / 0.80),
            "gamma_logit": math.log(0.35 / 0.65),
            "epsilon_logit": math.log(0.15 / 0.85),
        }
    }
    return V07BFixture(
        generator_model=generator_model,
        training_model=training_model,
        refusal_model=refusal_model,
        scoring_model=scoring_model,
        covariates=covariates,
        generating_theta=theta,
        generating_theta_obs={"joint": {}, "occupancy_calibration": {}},
        joint_train_keys=joint_train_keys,
        direct_train_keys=direct_train_keys,
        heldout_keys=heldout_keys,
    )
