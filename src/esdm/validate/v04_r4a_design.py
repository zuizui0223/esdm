"""Prospective phase-balanced observation design for v0.4-R4a."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from esdm.model import Model
from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
from .v04_r2_state_activity import build_v04_r2_fixture
from .v04_r3a_design import spatial_maximin_sequence


def phase_balanced_temporal_contexts(
    doy_values,
    hour_values,
) -> tuple[tuple[int, int], ...]:
    """Return the frozen 3-season × 4-hour Cartesian R4 temporal design."""

    doys = tuple(sorted(int(value) for value in doy_values))
    hours = tuple(sorted(int(value) for value in hour_values))
    if len(doys) != 6 or len(set(doys)) != 6:
        raise ValueError("R4 temporal design requires six unique DOY values")
    if len(hours) != 4 or len(set(hours)) != 4:
        raise ValueError("R4 temporal design requires four unique hour values")

    selected_doys = (doys[0], doys[2], doys[4])
    return tuple(
        (doy, hour)
        for doy in selected_doys
        for hour in hours
    )


@dataclass(frozen=True, slots=True)
class V04R4AFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    calibrated_spaces: tuple[str, ...]
    annotated_spaces: tuple[str, ...]
    annotated_times: tuple[tuple[int, int], ...]
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
        object.__setattr__(self, "calibrated_spaces", tuple(self.calibrated_spaces))
        object.__setattr__(self, "annotated_spaces", tuple(self.annotated_spaces))
        object.__setattr__(
            self,
            "annotated_times",
            tuple((int(doy), int(hour)) for doy, hour in self.annotated_times),
        )


def _r4a_annotated_stream(
    r2_fixture,
    annotated_spaces,
    annotated_times,
) -> StateAnnotatedCount:
    train_exposed = {
        (space, doy, hour)
        for space in annotated_spaces
        for doy, hour in annotated_times
    }
    heldout = set(r2_fixture.heldout_spaces)
    heldout_exposed = {
        key
        for key in r2_fixture.model.domain.keys
        if key[0] in heldout
    }
    return StateAnnotatedCount(
        name="annotated",
        state_space=r2_fixture.model.streams[2].state_space,
        effort=EffortField(
            {
                key: 8.0
                for key in (train_exposed | heldout_exposed)
            }
        ),
        detection=KnownDetection(probability=0.85),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )


def build_v04_r4a_fixture(source_csv_text: str) -> V04R4AFixture:
    """Build the prospective R4a fixture without evaluating identification."""

    r2 = build_v04_r2_fixture(source_csv_text, profile="positive")
    spatial = spatial_maximin_sequence(
        r2.train_spaces,
        r2.covariates,
        count=36,
    )
    temporal = phase_balanced_temporal_contexts(
        r2.model.domain.doy,
        r2.model.domain.hour,
    )
    if spatial[:18] != r2.calibration_spaces:
        raise RuntimeError(
            "R4a first 18 spatial sites must equal frozen R2 calibration sequence"
        )

    annotated = _r4a_annotated_stream(r2, spatial, temporal)
    model = Model(
        domain=r2.model.domain,
        species=r2.model.species,
        streams=(
            r2.model.streams[0],
            r2.model.streams[1],
            annotated,
        ),
    )
    model.check_design()

    return V04R4AFixture(
        model=model,
        covariates=r2.covariates,
        train_spaces=r2.train_spaces,
        heldout_spaces=r2.heldout_spaces,
        calibrated_spaces=r2.calibration_spaces,
        annotated_spaces=spatial,
        annotated_times=temporal,
        generating_theta=r2.generating_theta,
        generating_theta_obs=r2.generating_theta_obs,
    )
