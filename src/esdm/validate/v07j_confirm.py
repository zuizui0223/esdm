"""Fresh confirmatory stress worlds derived from the burned v0.7j surface."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .v07g_fixture import V07G_SELECTED_PLACEMENT
from .v07i_fixture import build_v07i_confirm_fixture


V07J_WORLDS = ("transfer_positive", "reversal")

V07J_WORLD_PROBABILITIES = {
    "transfer_positive": {
        "psi0": 0.20,
        "gamma": 0.15,
        "epsilon": 0.05,
    },
    "reversal": {
        "psi0": 0.80,
        "gamma": 0.15,
        "epsilon": 0.30,
    },
}


def _logit(probability: float) -> float:
    p = float(probability)
    return math.log(p / (1.0 - p))


def theta_for_v07j_world(world: str) -> dict:
    name = str(world)
    if name not in V07J_WORLD_PROBABILITIES:
        raise KeyError(f"unknown v0.7j stress world {name!r}")
    truth = V07J_WORLD_PROBABILITIES[name]
    return {
        "sp": {
            "alpha": 0.30,
            "psi0_logit": _logit(truth["psi0"]),
            "gamma_logit": _logit(truth["gamma"]),
            "epsilon_logit": _logit(truth["epsilon"]),
        }
    }


def truth_sites_for_v07j_world(world: str) -> dict:
    theta = theta_for_v07j_world(world)["sp"]
    return {
        "sp.suitability.alpha": theta["alpha"],
        "sp.occupancy.psi0_logit": theta["psi0_logit"],
        "sp.occupancy.gamma_logit": theta["gamma_logit"],
        "sp.occupancy.epsilon_logit": theta["epsilon_logit"],
    }


@dataclass(frozen=True, slots=True)
class V07JConfirmFixture:
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
    world: str


def build_v07j_confirm_fixture(world: str) -> V07JConfirmFixture:
    name = str(world)
    if name not in V07J_WORLDS:
        raise KeyError(f"unknown v0.7j stress world {name!r}")
    source = build_v07i_confirm_fixture(V07G_SELECTED_PLACEMENT)
    return V07JConfirmFixture(
        source=source,
        generator_model=source.generator_model,
        selected_model=source.selected_model,
        baseline_model=source.baseline_model,
        scoring_model=source.scoring_model,
        covariates=source.covariates,
        generating_theta=theta_for_v07j_world(name),
        generating_theta_obs=source.generating_theta_obs,
        selected_keys=source.selected_keys,
        baseline_keys=source.baseline_keys,
        heldout_keys=source.heldout_keys,
        world=name,
    )
