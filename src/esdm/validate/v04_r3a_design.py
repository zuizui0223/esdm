"""Deterministic budget-neutral design selectors for v0.4-R3a."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math

from esdm.model import Model
from esdm.observe import EffortField, KnownDetection, StateAnnotatedCount
from .v04_r2_state_activity import build_v04_r2_fixture


def _spatial_point(space, covariates) -> tuple[float, float]:
    key = (str(space), 15, 0)
    if key not in covariates:
        raise KeyError(f"missing selector covariates for {key!r}")
    values = covariates[key]
    if "precip_z_train" not in values:
        raise KeyError("precip_z_train")
    if "eastness_z_train" not in values:
        raise KeyError("eastness_z_train")
    point = (
        float(values["precip_z_train"]),
        float(values["eastness_z_train"]),
    )
    if any(not math.isfinite(value) for value in point):
        raise ValueError("spatial selector coordinates must be finite")
    return point


def spatial_maximin_sequence(
    train_spaces,
    covariates,
    *,
    count: int,
) -> tuple[str, ...]:
    """Return a deterministic environmental maximin sequence of training spaces."""

    spaces = tuple(str(space) for space in train_spaces)
    requested = int(count)
    if requested < 1 or requested > len(spaces):
        raise ValueError("invalid spatial maximin request")
    if len(set(spaces)) != len(spaces):
        raise ValueError("training spaces must be unique")

    points = {
        space: _spatial_point(space, covariates)
        for space in spaces
    }
    first = min(
        (
            (-(point[0] ** 2 + point[1] ** 2), space)
            for space, point in points.items()
        )
    )[1]
    selected = [first]
    remaining = set(spaces) - {first}

    while len(selected) < requested:
        scored = []
        for space in remaining:
            p, e = points[space]
            minimum_distance = min(
                (p - points[other][0]) ** 2
                + (e - points[other][1]) ** 2
                for other in selected
            )
            scored.append((-minimum_distance, space))
        chosen = min(scored)[1]
        selected.append(chosen)
        remaining.remove(chosen)

    return tuple(selected)


def _temporal_point(doy: int, hour: int) -> tuple[float, float, float, float]:
    season = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
    daily = 2.0 * math.pi * float(hour) / 24.0
    return (
        math.sin(season),
        math.cos(season),
        math.sin(daily),
        math.cos(daily),
    )


def temporal_maximin_sequence(
    doy_values,
    hour_values,
    *,
    count: int,
) -> tuple[tuple[int, int], ...]:
    """Return a deterministic maximin sequence in cyclic season/hour space."""

    candidates = tuple(
        sorted(
            (int(doy), int(hour))
            for doy in doy_values
            for hour in hour_values
        )
    )
    requested = int(count)
    if requested < 1 or requested > len(candidates):
        raise ValueError("invalid temporal maximin request")
    if len(set(candidates)) != len(candidates):
        raise ValueError("temporal candidates must be unique")

    points = {
        key: _temporal_point(*key)
        for key in candidates
    }
    selected = [candidates[0]]
    remaining = set(candidates) - {candidates[0]}

    while len(selected) < requested:
        scored = []
        for candidate in remaining:
            point = points[candidate]
            minimum_distance = min(
                sum(
                    (value - points[other][index]) ** 2
                    for index, value in enumerate(point)
                )
                for other in selected
            )
            stable_distance = round(minimum_distance, 12)
            scored.append((-stable_distance, candidate))
        chosen = min(scored)[1]
        selected.append(chosen)
        remaining.remove(chosen)

    return tuple(selected)



@dataclass(frozen=True, slots=True)
class V04R3AFixture:
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
        object.__setattr__(
            self,
            "calibrated_spaces",
            tuple(self.calibrated_spaces),
        )
        object.__setattr__(
            self,
            "annotated_spaces",
            tuple(self.annotated_spaces),
        )
        object.__setattr__(
            self,
            "annotated_times",
            tuple(
                (int(doy), int(hour))
                for doy, hour in self.annotated_times
            ),
        )


def _r3a_annotated_stream(
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


def build_v04_r3a_fixture(source_csv_text: str) -> V04R3AFixture:
    """Build the prospective R3a positive fixture without evaluating identification."""

    r2 = build_v04_r2_fixture(
        source_csv_text,
        profile="positive",
    )
    spatial = spatial_maximin_sequence(
        r2.train_spaces,
        r2.covariates,
        count=36,
    )
    temporal = temporal_maximin_sequence(
        r2.model.domain.doy,
        r2.model.domain.hour,
        count=12,
    )
    if spatial[:18] != r2.calibration_spaces:
        raise RuntimeError(
            "R3a first 18 spatial sites must equal frozen R2 calibration sequence"
        )

    annotated = _r3a_annotated_stream(
        r2,
        spatial,
        temporal,
    )
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

    return V04R3AFixture(
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
