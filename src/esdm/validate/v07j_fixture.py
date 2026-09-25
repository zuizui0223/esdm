"""Population-shift fixtures for v0.7j calibration-transfer robustness."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .v07g_fixture import build_v07g_validation_fixture


def _logit(probability: float) -> float:
    value = float(probability)
    if not 0.0 < value < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    return math.log(value / (1.0 - value))


V07J_TARGET_WORLDS = {
    "low_occupancy": {
        "alpha": 0.30,
        "psi0": 0.10,
        "gamma": 0.20,
        "epsilon": 0.30,
    },
    "high_occupancy": {
        "alpha": 0.30,
        "psi0": 0.50,
        "gamma": 0.55,
        "epsilon": 0.10,
    },
    "high_turnover": {
        "alpha": 0.30,
        "psi0": 0.20,
        "gamma": 0.55,
        "epsilon": 0.40,
    },
}

V07J_WORLD_ORDER = (
    "low_occupancy",
    "high_occupancy",
    "high_turnover",
)


def truth_sites(world: str) -> dict[str, float]:
    if world not in V07J_TARGET_WORLDS:
        raise KeyError(f"unknown v0.7j target world {world!r}")
    row = V07J_TARGET_WORLDS[world]
    return {
        "sp.suitability.alpha": float(row["alpha"]),
        "sp.occupancy.psi0_logit": _logit(float(row["psi0"])),
        "sp.occupancy.gamma_logit": _logit(float(row["gamma"])),
        "sp.occupancy.epsilon_logit": _logit(float(row["epsilon"])),
    }


def theta_for_world(world: str) -> dict:
    sites = truth_sites(world)
    return {
        "sp": {
            "alpha": sites["sp.suitability.alpha"],
            "psi0_logit": sites["sp.occupancy.psi0_logit"],
            "gamma_logit": sites["sp.occupancy.gamma_logit"],
            "epsilon_logit": sites["sp.occupancy.epsilon_logit"],
        }
    }


@dataclass(frozen=True, slots=True)
class V07JFixture:
    world: str
    source: object
    generator_model: object
    selected_model: object
    baseline_model: object
    scoring_model: object
    covariates: dict
    generating_theta: dict
    generating_theta_obs: dict
    selected_keys: tuple
    baseline_keys: tuple
    heldout_keys: tuple


def build_v07j_fixture(world: str) -> V07JFixture:
    source = build_v07g_validation_fixture()
    return V07JFixture(
        world=str(world),
        source=source.source,
        generator_model=source.generator_model,
        selected_model=source.optimized_model,
        baseline_model=source.baseline_model,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=theta_for_world(world),
        generating_theta_obs=source.generating_theta_obs,
        selected_keys=source.optimized_keys,
        baseline_keys=source.baseline_keys,
        heldout_keys=source.heldout_keys,
    )
