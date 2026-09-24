"""Fresh known-truth accessibility design for v0.6a."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import (
    AccessibilityCount,
    AccessiblePresenceOnly,
    EffortField,
)
from esdm.process import LinearAccessibility, LinearSuitability


V06A_RECOVERY_TRUTH = {
    "sp.suitability.suitability_intercept": 0.30,
    "sp.suitability.beta_habitat": 0.75,
    "sp.accessibility.access_intercept": 0.40,
    "sp.accessibility.beta_distance": -1.10,
}

V06A_REFUSAL_TARGETS = (
    "sp.suitability.suitability_intercept",
    "sp.accessibility.access_intercept",
)


@dataclass(frozen=True, slots=True)
class V06AFixture:
    model: Model
    covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    generating_theta_obs: dict

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType({
                key: MappingProxyType(dict(values))
                for key, values in self.covariates.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType({
                species: MappingProxyType(dict(values))
                for species, values in self.generating_theta.items()
            }),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType({
                stream: MappingProxyType(dict(values))
                for stream, values in self.generating_theta_obs.items()
            }),
        )


def _covariate_rows(n: int = 36):
    rows = []
    for index in range(n):
        habitat = (
            math.sin(2.0 * math.pi * index / 12.0)
            + 0.35 * math.cos(2.0 * math.pi * index / 5.0)
        )
        distance = (
            math.cos(2.0 * math.pi * index / 9.0)
            + 0.25 * math.sin(2.0 * math.pi * index / 7.0)
        )
        rows.append({
            "habitat": float(habitat),
            "distance": float(distance),
        })
    return tuple(rows)


def build_v06a_fixture() -> V06AFixture:
    spaces = tuple(f"s{index:02d}" for index in range(36))
    train_spaces = spaces[:24]
    heldout_spaces = spaces[24:]
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    rows = _covariate_rows(len(spaces))
    covariates = {
        key: dict(rows[index])
        for index, key in enumerate(grid.keys)
    }

    processes = (
        LinearSuitability(
            covariates=("habitat",),
            intercept_parameter="suitability_intercept",
            coefficient_parameters={"habitat": "beta_habitat"},
        ),
        LinearAccessibility(
            covariates=("distance",),
            intercept_parameter="access_intercept",
            coefficient_parameters={"distance": "beta_distance"},
        ),
    )

    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    direct = AccessibilityCount(
        "access",
        effort=EffortField({
            key: 20.0
            for key in grid.keys
            if key[0] in set(train_spaces)
        }),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": processes},
        streams=(joint, direct),
    )
    model.check_design()

    theta = {
        "sp": {
            "suitability_intercept": 0.30,
            "beta_habitat": 0.75,
            "access_intercept": 0.40,
            "beta_distance": -1.10,
        }
    }
    return V06AFixture(
        model=model,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        generating_theta=theta,
        generating_theta_obs={"joint": {}, "access": {}},
    )


def build_v06a_joint_only_refusal():
    """Exact product-confounding negative control with two free intercepts."""

    spaces = tuple(f"r{index:02d}" for index in range(12))
    grid = Grid(space=spaces, doy=(1,), hour=(0,))
    covariates = {key: {} for key in grid.keys}
    processes = (
        LinearSuitability(
            covariates=(),
            intercept_parameter="suitability_intercept",
            coefficient_parameters={},
        ),
        LinearAccessibility(
            covariates=(),
            intercept_parameter="access_intercept",
            coefficient_parameters={},
        ),
    )
    joint = AccessiblePresenceOnly(
        "joint",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        informs=frozenset({"suitability", "accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(grid, {"sp": processes}, (joint,))
    model.check_design()
    theta = {
        "sp": {
            "suitability_intercept": 0.30,
            "access_intercept": 0.40,
        }
    }
    return model, covariates, theta, {"joint": {}}
