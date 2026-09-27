"""Analytic known-truth worlds for interaction claim boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


JointKey = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class BinaryInteractionWorld:
    """Exact joint distribution over measured environment, target, and partner state."""

    name: str
    joint: Mapping[JointKey, float]
    interaction_truth: bool
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("world name must be non-empty")
        checked: dict[JointKey, float] = {}
        for key, raw in self.joint.items():
            if len(key) != 3 or any(value not in (0, 1) for value in key):
                raise ValueError("known-truth world keys must be binary (environment, target, partner)")
            probability = float(raw)
            if not math.isfinite(probability) or probability < 0.0:
                raise ValueError("joint probabilities must be finite and non-negative")
            checked[key] = probability
        if not math.isclose(sum(checked.values()), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("joint probabilities must sum to one")
        object.__setattr__(self, "joint", checked)


def _bernoulli_probability(state: int, positive_probability: float) -> float:
    return positive_probability if state == 1 else 1.0 - positive_probability


def observed_shared_environment_world() -> BinaryInteractionWorld:
    """Both taxa respond to measured environment but are independent conditional on it."""

    target_positive = {0: 0.20, 1: 0.80}
    partner_positive = {0: 0.30, 1: 0.70}
    joint: dict[JointKey, float] = {}
    for environment in (0, 1):
        for target in (0, 1):
            for partner in (0, 1):
                joint[(environment, target, partner)] = (
                    0.5
                    * _bernoulli_probability(target, target_positive[environment])
                    * _bernoulli_probability(partner, partner_positive[environment])
                )
    return BinaryInteractionWorld(
        name="observed_shared_environment",
        joint=joint,
        interaction_truth=False,
        description="Measured environment drives both taxa; conditional independence is exact.",
    )


def hidden_shared_driver_world() -> BinaryInteractionWorld:
    """A hidden common driver creates predictive dependence without interaction."""

    joint: dict[JointKey, float] = {(0, target, partner): 0.0 for target in (0, 1) for partner in (0, 1)}
    for hidden_driver in (0, 1):
        target_positive = 0.10 if hidden_driver == 0 else 0.90
        partner_positive = 0.10 if hidden_driver == 0 else 0.90
        for target in (0, 1):
            for partner in (0, 1):
                joint[(0, target, partner)] += (
                    0.5
                    * _bernoulli_probability(target, target_positive)
                    * _bernoulli_probability(partner, partner_positive)
                )
    return BinaryInteractionWorld(
        name="hidden_shared_driver",
        joint=joint,
        interaction_truth=False,
        description="An omitted driver induces association although no biotic edge generates target state.",
    )


def directed_biotic_coupling_world() -> BinaryInteractionWorld:
    """Partner state directly changes target-state probability after measured conditioning."""

    joint: dict[JointKey, float] = {}
    for environment in (0, 1):
        for partner in (0, 1):
            partner_probability = 0.5
            target_positive = 0.15 if partner == 0 else 0.85
            for target in (0, 1):
                joint[(environment, target, partner)] = (
                    0.5
                    * partner_probability
                    * _bernoulli_probability(target, target_positive)
                )
    return BinaryInteractionWorld(
        name="directed_biotic_coupling",
        joint=joint,
        interaction_truth=True,
        description="Partner state is part of the generating mechanism for target state.",
    )


def oracle_biotic_information_gain(world: BinaryInteractionWorld) -> float:
    """Expected log-score gain from P(target|environment,partner) over P(target|environment)."""

    environment_mass: dict[int, float] = {0: 0.0, 1: 0.0}
    environment_target_mass: dict[tuple[int, int], float] = {}
    environment_partner_mass: dict[tuple[int, int], float] = {}

    for (environment, target, partner), probability in world.joint.items():
        environment_mass[environment] += probability
        environment_target_mass[(environment, target)] = (
            environment_target_mass.get((environment, target), 0.0) + probability
        )
        environment_partner_mass[(environment, partner)] = (
            environment_partner_mass.get((environment, partner), 0.0) + probability
        )

    gain = 0.0
    for (environment, target, partner), probability in world.joint.items():
        if probability <= 0.0:
            continue
        baseline = environment_target_mass[(environment, target)] / environment_mass[environment]
        augmented = probability / environment_partner_mass[(environment, partner)]
        gain += probability * (math.log(augmented) - math.log(baseline))
    return gain
