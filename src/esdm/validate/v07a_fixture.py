"""Fresh structural-identification fixture for v0.7a dynamic occupancy."""

from __future__ import annotations

from dataclasses import dataclass
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, OccupancyCount, OccupiedPresenceOnly
from esdm.process import ColonizationExtinctionOccupancy, LinearSuitability


V07A_TRUTH = {
    "sp.suitability.alpha": 0.30,
    "sp.occupancy.psi0_logit": math.log(0.20 / 0.80),
    "sp.occupancy.gamma_logit": math.log(0.35 / 0.65),
    "sp.occupancy.epsilon_logit": math.log(0.15 / 0.85),
}


@dataclass(frozen=True, slots=True)
class V07AFixture:
    positive_model: Model
    refusal_model: Model
    covariates: dict
    theta: dict
    theta_obs_positive: dict
    theta_obs_refusal: dict


def build_v07a_fixture() -> V07AFixture:
    grid = Grid(
        space=("trajectory",),
        doy=tuple(range(1, 13)),
        hour=(0,),
    )
    covariates = {key: {} for key in grid.keys}
    processes = (
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
    joint = OccupiedPresenceOnly(
        "joint",
        effort=EffortField({key: 500.0 for key in grid.keys}),
        informs=frozenset({"suitability", "occupancy"}),
        targets=frozenset({"sp"}),
    )
    calibration_keys = set(grid.keys[:4])
    direct = OccupancyCount(
        "occupancy_calibration",
        effort=EffortField({
            key: 500.0
            for key in grid.keys
            if key in calibration_keys
        }),
        informs=frozenset({"occupancy"}),
        targets=frozenset({"sp"}),
    )
    positive = Model(
        grid,
        {"sp": processes},
        (joint, direct),
    )
    refusal = Model(
        grid,
        {"sp": processes},
        (joint,),
    )
    positive.check_design()
    refusal.check_design()
    theta = {
        "sp": {
            "alpha": 0.30,
            "psi0_logit": math.log(0.20 / 0.80),
            "gamma_logit": math.log(0.35 / 0.65),
            "epsilon_logit": math.log(0.15 / 0.85),
        }
    }
    return V07AFixture(
        positive_model=positive,
        refusal_model=refusal,
        covariates=covariates,
        theta=theta,
        theta_obs_positive={"joint": {}, "occupancy_calibration": {}},
        theta_obs_refusal={"joint": {}},
    )
