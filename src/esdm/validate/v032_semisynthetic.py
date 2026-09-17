"""Frozen v0.3.2 semi-synthetic separation fixture.

This module defines geometry and known truth only. It does not inspect fitted outcomes
and it does not make scientific claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math
import statistics

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, LogLinearEffort, PresenceOnly
from esdm.process import LinearSuitability
from .v031_semisynthetic import (
    SemiSyntheticStation,
    V031_SEMISYNTHETIC_MANIFEST,
    V031SemiSyntheticManifest,
    parse_station_csv,
)


@dataclass(frozen=True, slots=True)
class V032SemiSyntheticFixture:
    model: Model
    stations: tuple[SemiSyntheticStation, ...]
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    calibration_spaces: tuple[str, ...]
    profile: str
    generating_theta: Mapping[str, Mapping[str, float]]
    generating_theta_obs: Mapping[str, Mapping[str, float]]
    manifest: V031SemiSyntheticManifest

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {key: MappingProxyType(dict(values)) for key, values in self.covariates.items()}
            ),
        )
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType(
                {name: MappingProxyType(dict(values)) for name, values in self.generating_theta.items()}
            ),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType(
                {name: MappingProxyType(dict(values)) for name, values in self.generating_theta_obs.items()}
            ),
        )


def _block(longitude: float) -> str:
    if longitude < -110.0:
        return "west"
    if longitude < -85.0:
        return "central"
    return "east"


def _training_standardize(
    stations: tuple[SemiSyntheticStation, ...],
    train_spaces: tuple[str, ...],
    getter,
) -> dict[str, float]:
    training = tuple(getter(station) for station in stations if station.station_id in set(train_spaces))
    mean = statistics.fmean(training)
    sd = statistics.pstdev(training)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("training covariate must have positive finite variation")
    return {station.station_id: (getter(station) - mean) / sd for station in stations}


def _positive_calibration_spaces(
    train_spaces: tuple[str, ...],
    precip_by_space: Mapping[str, float],
) -> tuple[str, ...]:
    ordered = tuple(sorted(train_spaces, key=lambda space: (precip_by_space[space], space)))
    if len(ordered) < 12:
        raise ValueError("positive calibration profile requires at least 12 training stations")
    ranks = []
    for k in range(12):
        raw = k * (len(ordered) - 1) / 11.0
        ranks.append(int(math.floor(raw + 0.5)))
    selected = tuple(ordered[index] for index in ranks)
    if len(set(selected)) != 12:
        raise ValueError("positive calibration quantiles did not yield 12 unique stations")
    return selected


def _negative_calibration_spaces(
    train_spaces: tuple[str, ...],
    precip_by_space: Mapping[str, float],
) -> tuple[str, ...]:
    selected = min(train_spaces, key=lambda space: (abs(precip_by_space[space]), space))
    return (selected,)


def build_v032_semisynthetic_fixture(
    source_csv_text: str,
    *,
    profile: str = "positive",
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V032SemiSyntheticFixture:
    """Build the frozen F-prime fixture before any outcome inspection."""

    normalized_profile = str(profile).strip().lower()
    if normalized_profile not in {"positive", "negative"}:
        raise ValueError("profile must be 'positive' or 'negative'")

    stations = parse_station_csv(source_csv_text, rows=manifest.station_rows)
    spaces = tuple(station.station_id for station in stations)
    block_by_space = {station.station_id: _block(station.longitude) for station in stations}
    train_spaces = tuple(space for space in spaces if block_by_space[space] != "east")
    heldout_spaces = tuple(space for space in spaces if block_by_space[space] == "east")
    if not train_spaces or not heldout_spaces:
        raise ValueError("v0.3.2 fixture requires non-empty training and east held-out blocks")

    precip = _training_standardize(stations, train_spaces, lambda station: station.average_precip)
    latitude = _training_standardize(stations, train_spaces, lambda station: station.latitude)
    eastness = _training_standardize(stations, train_spaces, lambda station: station.longitude)

    if min(eastness[space] for space in heldout_spaces) <= max(
        eastness[space] for space in train_spaces
    ):
        raise ValueError("east held-out block is not outside the training eastness range")

    calibration_spaces = (
        _positive_calibration_spaces(train_spaces, precip)
        if normalized_profile == "positive"
        else _negative_calibration_spaces(train_spaces, precip)
    )

    grid = Grid(space=spaces, doy=manifest.doy_bins, hour=manifest.hour_bins)
    covariates = {
        key: {
            "precip_z_train": float(precip[key[0]]),
            "lat_z_train": float(latitude[key[0]]),
            "eastness_z_train": float(eastness[key[0]]),
        }
        for key in grid.keys
    }

    suitability = LinearSuitability(
        covariates=("precip_z_train", "lat_z_train", "eastness_z_train"),
        intercept_parameter="intercept",
        coefficient_parameters={
            "precip_z_train": "beta_precip",
            "lat_z_train": "beta_lat",
            "eastness_z_train": "beta_eastness",
        },
    )
    opportunistic = PresenceOnly(
        name="opportunistic",
        effort=LogLinearEffort(
            baseline=4.0,
            covariate="precip_z_train",
            coefficient_parameter="gamma_precip",
        ),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    calibration_set = set(calibration_spaces)
    calibrated = PresenceOnly(
        name="calibrated",
        effort=EffortField(
            {key: 3.0 for key in grid.keys if key[0] in calibration_set}
        ),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (suitability,)},
        streams=(opportunistic, calibrated),
    )
    model.check_design()

    return V032SemiSyntheticFixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        calibration_spaces=calibration_spaces,
        profile=normalized_profile,
        generating_theta={
            "sp": {
                "intercept": -2.0,
                "beta_precip": 0.45,
                "beta_lat": -0.20,
                "beta_eastness": 0.35,
            }
        },
        generating_theta_obs={
            "opportunistic": {"gamma_precip": 0.40},
            "calibrated": {},
        },
        manifest=manifest,
    )


def v032_identification_anchors(fixture: V032SemiSyntheticFixture):
    """Return the three frozen pre-outcome identification anchors."""

    truth_theta = {name: dict(values) for name, values in fixture.generating_theta.items()}
    truth_obs = {name: dict(values) for name, values in fixture.generating_theta_obs.items()}

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"]["intercept"] = -1.7
    theta_b["sp"]["beta_precip"] = 0.70
    obs_b["opportunistic"]["gamma_precip"] = 0.15

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"]["intercept"] = -2.3
    theta_c["sp"]["beta_precip"] = 0.20
    obs_c["opportunistic"]["gamma_precip"] = 0.65

    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )
