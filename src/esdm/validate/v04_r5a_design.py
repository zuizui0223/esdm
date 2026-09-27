"""Prospective direct state-composition calibration design for v0.4-R5a."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from esdm.model import Model
from esdm.observe import EffortField, StateCompositionCount
from .v04_r4a_design import build_v04_r4a_fixture


@dataclass(frozen=True, slots=True)
class V04R5AFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    calibrated_spaces: tuple[str, ...]
    annotated_spaces: tuple[str, ...]
    annotated_times: tuple[tuple[int, int], ...]
    state_calibration_spaces: tuple[str, ...]
    state_calibration_times: tuple[tuple[int, int], ...]
    generating_theta: Mapping[str, Mapping[str, float]]
    generating_theta_obs: Mapping[str, Mapping[str, float]]
    profile: str = "positive"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {
                    key: MappingProxyType(dict(values))
                    for key, values in self.covariates.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType(
                {
                    name: MappingProxyType(dict(values))
                    for name, values in self.generating_theta.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType(
                {
                    name: MappingProxyType(dict(values))
                    for name, values in self.generating_theta_obs.items()
                }
            ),
        )
        for name in (
            "calibrated_spaces",
            "annotated_spaces",
            "state_calibration_spaces",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        for name in ("annotated_times", "state_calibration_times"):
            object.__setattr__(
                self,
                name,
                tuple((int(doy), int(hour)) for doy, hour in getattr(self, name)),
            )


def build_v04_r5a_fixture(source_csv_text: str) -> V04R5AFixture:
    """Build the prospective R5a positive fixture without evaluating identification."""

    r4 = build_v04_r4a_fixture(source_csv_text)
    exposed = {
        (space, doy, hour)
        for space in r4.annotated_spaces
        for doy, hour in r4.annotated_times
    }
    state_calibration = StateCompositionCount(
        name="state_calibration",
        state_space=r4.model.streams[2].state_space,
        effort=EffortField({key: 1.0 for key in exposed}),
        informs=frozenset({"state"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=r4.model.domain,
        species=r4.model.species,
        streams=(*r4.model.streams, state_calibration),
    )
    model.check_design()

    theta_obs = {
        name: dict(values)
        for name, values in r4.generating_theta_obs.items()
    }
    theta_obs["state_calibration"] = {}

    return V04R5AFixture(
        model=model,
        covariates=r4.covariates,
        train_spaces=r4.train_spaces,
        heldout_spaces=r4.heldout_spaces,
        calibrated_spaces=r4.calibrated_spaces,
        annotated_spaces=r4.annotated_spaces,
        annotated_times=r4.annotated_times,
        state_calibration_spaces=r4.annotated_spaces,
        state_calibration_times=r4.annotated_times,
        generating_theta=r4.generating_theta,
        generating_theta_obs=theta_obs,
    )
