"""Budget-matched accessibility-evidence benchmark for v0.6c."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import AccessibilityCount, AccessiblePresenceOnly, EffortField
from .v06a_fixture import V06A_RECOVERY_TRUTH, build_v06a_fixture


V06C_MATCHED_JOINT_EFFORT = 12.168687798294679
V06C_ACCESS_TARGETS = (
    "sp.accessibility.access_intercept",
    "sp.accessibility.beta_distance",
)


@dataclass(frozen=True, slots=True)
class V06CFixture:
    model: Model
    covariates: dict
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    generating_theta: dict
    generating_theta_obs: dict
    expected_direct_aux_count: float
    expected_matched_aux_count: float

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

    @property
    def relative_budget_error(self) -> float:
        denom = max(abs(self.expected_direct_aux_count), 1e-15)
        return abs(
            self.expected_direct_aux_count - self.expected_matched_aux_count
        ) / denom


def build_v06c_fixture() -> V06CFixture:
    base = build_v06a_fixture()
    grid = base.model.domain
    train = set(base.train_spaces)
    processes = base.model.species["sp"]

    base_joint = AccessiblePresenceOnly(
        "base_joint",
        effort=EffortField({key: 8.0 for key in grid.keys}),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    direct = AccessibilityCount(
        "direct_access",
        effort=EffortField({
            key: 20.0 for key in grid.keys if key[0] in train
        }),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    matched = AccessiblePresenceOnly(
        "matched_joint",
        effort=EffortField({
            key: V06C_MATCHED_JOINT_EFFORT
            for key in grid.keys
            if key[0] in train
        }),
        informs=frozenset({"accessibility"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        grid,
        {"sp": processes},
        (base_joint, direct, matched),
    )
    model.check_design()

    theta = {
        species: dict(values)
        for species, values in base.generating_theta.items()
    }
    theta_obs = {
        "base_joint": {},
        "direct_access": {},
        "matched_joint": {},
    }
    fields = model.latent_fields(theta, base.covariates)
    direct_rates = direct.expected_rates(
        "sp", fields, theta_obs={}, covariates=base.covariates
    )
    matched_rates = matched.expected_rates(
        "sp", fields, theta_obs={}, covariates=base.covariates
    )
    return V06CFixture(
        model=model,
        covariates={
            key: dict(values)
            for key, values in base.covariates.items()
        },
        train_spaces=base.train_spaces,
        heldout_spaces=base.heldout_spaces,
        generating_theta=theta,
        generating_theta_obs=theta_obs,
        expected_direct_aux_count=math.fsum(direct_rates.values()),
        expected_matched_aux_count=math.fsum(matched_rates.values()),
    )


def v06c_condition_model(fixture: V06CFixture, condition: str, spaces):
    name = str(condition)
    if name not in {"direct", "matched_joint", "heldout"}:
        raise ValueError("unknown v0.6c condition")
    grid = Grid(
        space=tuple(spaces),
        doy=fixture.model.domain.doy,
        hour=fixture.model.domain.hour,
    )
    streams = {stream.name: stream for stream in fixture.model.streams}
    if name == "direct":
        selected = (streams["base_joint"], streams["direct_access"])
    elif name == "matched_joint":
        selected = (streams["base_joint"], streams["matched_joint"])
    else:
        base_joint = streams["base_joint"]
        heldout_joint = AccessiblePresenceOnly(
            "base_joint",
            effort=base_joint.effort,
            informs=frozenset({"suitability", "accessibility"}),
            detection_probability=base_joint.detection_probability,
            detection=base_joint.detection,
            targets=base_joint.targets,
        )
        selected = (heldout_joint,)
    model = Model(
        grid,
        fixture.model.species,
        selected,
    )
    model.check_design()
    covariates = {
        key: dict(fixture.covariates[key])
        for key in grid.keys
    }
    return model, covariates
