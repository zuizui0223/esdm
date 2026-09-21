"""Frozen v0.4-R2 hard separation fixture.

Defines the three-stream geometry, spatial/temporal covariates, known truth, and
identification anchors only. No fitted outcomes are inspected here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
import math
import statistics

from esdm.domain import Grid, StateSpace
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    LogitDetection,
    MultiLogLinearEffort,
    PresenceOnly,
    StateAnnotatedCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability
from .v031_semisynthetic import (
    SemiSyntheticStation,
    V031_SEMISYNTHETIC_MANIFEST,
    V031SemiSyntheticManifest,
    parse_station_csv,
)


@dataclass(frozen=True, slots=True)
class V04R2Fixture:
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
    train_set = set(train_spaces)
    values = tuple(
        getter(station)
        for station in stations
        if station.station_id in train_set
    )
    mean = statistics.fmean(values)
    sd = statistics.pstdev(values)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("training covariate must have positive finite variation")
    return {
        station.station_id: (getter(station) - mean) / sd
        for station in stations
    }


def _temporal_covariates(doy: int, hour: int) -> dict[str, float]:
    season_angle = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
    hour_angle = 2.0 * math.pi * float(hour) / 24.0
    return {
        "season_sin": math.sin(season_angle),
        "season_cos": math.cos(season_angle),
        "hour_sin": math.sin(hour_angle),
        "hour_cos": math.cos(hour_angle),
    }


def _base_geometry(
    source_csv_text: str,
    manifest: V031SemiSyntheticManifest,
):
    stations = parse_station_csv(source_csv_text, rows=manifest.station_rows)
    spaces = tuple(station.station_id for station in stations)
    block_by_space = {
        station.station_id: _block(station.longitude)
        for station in stations
    }
    train_spaces = tuple(
        space for space in spaces if block_by_space[space] != "east"
    )
    heldout_spaces = tuple(
        space for space in spaces if block_by_space[space] == "east"
    )
    if not train_spaces or not heldout_spaces:
        raise ValueError("R2 fixture requires non-empty train and east-heldout blocks")

    precip = _training_standardize(
        stations,
        train_spaces,
        lambda station: station.average_precip,
    )
    latitude = _training_standardize(
        stations,
        train_spaces,
        lambda station: station.latitude,
    )
    eastness = _training_standardize(
        stations,
        train_spaces,
        lambda station: station.longitude,
    )
    if min(eastness[space] for space in heldout_spaces) <= max(
        eastness[space] for space in train_spaces
    ):
        raise ValueError("east held-out block is not outside the training eastness range")

    grid = Grid(
        space=spaces,
        doy=manifest.doy_bins,
        hour=manifest.hour_bins,
    )
    covariates = {}
    for key in grid.keys:
        temporal = _temporal_covariates(key[1], key[2])
        covariates[key] = {
            "precip_z_train": float(precip[key[0]]),
            "lat_z_train": float(latitude[key[0]]),
            "eastness_z_train": float(eastness[key[0]]),
            **temporal,
        }
    return (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        precip,
        eastness,
    )


def _positive_calibration_spaces(
    train_spaces: tuple[str, ...],
    precip: Mapping[str, float],
    eastness: Mapping[str, float],
) -> tuple[str, ...]:
    if len(train_spaces) < 18:
        raise ValueError("positive R2 profile requires at least 18 training spaces")

    points = {
        space: (float(precip[space]), float(eastness[space]))
        for space in train_spaces
    }
    first = min(
        (
            (-(point[0] ** 2 + point[1] ** 2), space)
            for space, point in points.items()
        )
    )[1]
    selected = [first]
    remaining = set(train_spaces) - {first}

    while len(selected) < 18:
        candidates = []
        for space in remaining:
            p, e = points[space]
            minimum_distance = min(
                (p - points[other][0]) ** 2
                + (e - points[other][1]) ** 2
                for other in selected
            )
            candidates.append((-minimum_distance, space))
        chosen = min(candidates)[1]
        selected.append(chosen)
        remaining.remove(chosen)
    return tuple(selected)


def _sparse_calibration_spaces(
    train_spaces: tuple[str, ...],
    precip: Mapping[str, float],
    eastness: Mapping[str, float],
) -> tuple[str, ...]:
    if len(train_spaces) < 4:
        raise ValueError("sparse R2 profile requires at least four training spaces")
    ordered = sorted(
        train_spaces,
        key=lambda space: (
            float(precip[space]) ** 2 + float(eastness[space]) ** 2,
            space,
        ),
    )
    return tuple(ordered[:4])


def _suitability() -> LinearSuitability:
    return LinearSuitability(
        covariates=(
            "precip_z_train",
            "lat_z_train",
            "eastness_z_train",
        ),
        intercept_parameter="intercept",
        coefficient_parameters={
            "precip_z_train": "beta_precip",
            "lat_z_train": "beta_lat",
            "eastness_z_train": "beta_eastness",
        },
    )


def _activity(*, intercept_only: bool = False) -> LinearActivity:
    if intercept_only:
        return LinearActivity(
            covariates=(),
            intercept_parameter="activity_intercept",
            coefficient_parameters={},
        )
    return LinearActivity(
        covariates=(
            "precip_z_train",
            "eastness_z_train",
            "season_sin",
            "hour_sin",
        ),
        intercept_parameter="activity_intercept",
        coefficient_parameters={
            "precip_z_train": "activity_beta_precip",
            "eastness_z_train": "activity_beta_eastness",
            "season_sin": "activity_beta_season",
            "hour_sin": "activity_beta_hour",
        },
    )


def _state() -> LinearState:
    states = StateSpace(("resting", "foraging"))
    return LinearState(
        state_space=states,
        reference_state="resting",
        covariates=(
            "precip_z_train",
            "eastness_z_train",
            "season_cos",
            "hour_cos",
        ),
        intercept_parameters={"foraging": "alpha_foraging"},
        coefficient_parameters={
            "foraging": {
                "precip_z_train": "beta_foraging_precip",
                "eastness_z_train": "beta_foraging_eastness",
                "season_cos": "beta_foraging_season",
                "hour_cos": "beta_foraging_hour",
            }
        },
    )


def _opportunistic_stream(grid: Grid) -> PresenceOnly:
    return PresenceOnly(
        name="opportunistic",
        effort=MultiLogLinearEffort(
            baseline=4.0,
            covariates=(
                "precip_z_train",
                "season_cos",
                "hour_sin",
            ),
            coefficient_parameters={
                "precip_z_train": "gamma_precip",
                "season_cos": "gamma_season",
                "hour_sin": "gamma_hour",
            },
        ),
        detection=LogitDetection("detection_intercept"),
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )


def _calibrated_stream(
    grid: Grid,
    calibration_spaces: tuple[str, ...],
) -> PresenceOnly:
    calibration = set(calibration_spaces)
    return PresenceOnly(
        name="calibrated",
        effort=EffortField(
            {
                key: 3.0
                for key in grid.keys
                if key[0] in calibration
            }
        ),
        detection_probability=0.90,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )


def _annotated_stream(
    grid: Grid,
    calibration_spaces: tuple[str, ...],
    heldout_spaces: tuple[str, ...],
    *,
    unknown_detection: bool,
) -> StateAnnotatedCount:
    exposed = set(calibration_spaces) | set(heldout_spaces)
    detection = (
        LogitDetection("detection_intercept")
        if unknown_detection
        else KnownDetection(probability=0.85)
    )
    return StateAnnotatedCount(
        name="annotated",
        state_space=StateSpace(("resting", "foraging")),
        effort=EffortField(
            {
                key: 8.0
                for key in grid.keys
                if key[0] in exposed
            }
        ),
        detection=detection,
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )


def _positive_theta() -> dict[str, dict[str, float]]:
    return {
        "sp": {
            "intercept": -2.0,
            "beta_precip": 0.45,
            "beta_lat": -0.20,
            "beta_eastness": 0.35,
            "activity_intercept": -0.35,
            "activity_beta_precip": 0.50,
            "activity_beta_eastness": 0.35,
            "activity_beta_season": 0.55,
            "activity_beta_hour": 0.40,
            "alpha_foraging": 0.20,
            "beta_foraging_precip": -0.45,
            "beta_foraging_eastness": 0.40,
            "beta_foraging_season": 0.50,
            "beta_foraging_hour": -0.45,
        }
    }


def _positive_theta_obs() -> dict[str, dict[str, float]]:
    return {
        "opportunistic": {
            "gamma_precip": 0.35,
            "gamma_season": 0.30,
            "gamma_hour": -0.25,
            "detection_intercept": -0.20,
        },
        "calibrated": {},
        "annotated": {},
    }


def build_v04_r2_fixture(
    source_csv_text: str,
    *,
    profile: str = "positive",
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V04R2Fixture:
    normalized = str(profile).strip().lower()
    if normalized not in {"positive", "sparse"}:
        raise ValueError("profile must be 'positive' or 'sparse'")

    (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        precip,
        eastness,
    ) = _base_geometry(source_csv_text, manifest)

    calibration_spaces = (
        _positive_calibration_spaces(train_spaces, precip, eastness)
        if normalized == "positive"
        else _sparse_calibration_spaces(train_spaces, precip, eastness)
    )
    model = Model(
        domain=grid,
        species={"sp": (_suitability(), _activity(), _state())},
        streams=(
            _opportunistic_stream(grid),
            _calibrated_stream(grid, calibration_spaces),
            _annotated_stream(
                grid,
                calibration_spaces,
                heldout_spaces,
                unknown_detection=False,
            ),
        ),
    )
    model.check_design()

    return V04R2Fixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        calibration_spaces=calibration_spaces,
        profile=normalized,
        generating_theta=_positive_theta(),
        generating_theta_obs=_positive_theta_obs(),
        manifest=manifest,
    )


def build_v04_r2_unknown_detection_fixture(
    source_csv_text: str,
    *,
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V04R2Fixture:
    (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        precip,
        eastness,
    ) = _base_geometry(source_csv_text, manifest)
    calibration_spaces = _positive_calibration_spaces(
        train_spaces,
        precip,
        eastness,
    )
    model = Model(
        domain=grid,
        species={
            "sp": (
                _suitability(),
                _activity(intercept_only=True),
                _state(),
            )
        },
        streams=(
            _opportunistic_stream(grid),
            _calibrated_stream(grid, calibration_spaces),
            _annotated_stream(
                grid,
                calibration_spaces,
                heldout_spaces,
                unknown_detection=True,
            ),
        ),
    )
    model.check_design()

    theta = _positive_theta()
    theta["sp"] = {
        key: value
        for key, value in theta["sp"].items()
        if not key.startswith("activity_beta_")
    }
    theta_obs = _positive_theta_obs()
    theta_obs["annotated"] = {"detection_intercept": 0.40}
    return V04R2Fixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        calibration_spaces=calibration_spaces,
        profile="unknown_detection",
        generating_theta=theta,
        generating_theta_obs=theta_obs,
        manifest=manifest,
    )


def _copy_state(fixture: V04R2Fixture):
    return (
        {
            name: dict(values)
            for name, values in fixture.generating_theta.items()
        },
        {
            name: dict(values)
            for name, values in fixture.generating_theta_obs.items()
        },
    )


def v04_r2_identification_anchors(fixture: V04R2Fixture):
    if fixture.profile not in {"positive", "sparse"}:
        raise ValueError("R2 known-detection anchors require positive or sparse fixture")

    truth_theta, truth_obs = _copy_state(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"].update(
        {
            "beta_precip": 0.70,
            "activity_intercept": -0.05,
            "activity_beta_precip": 0.70,
            "activity_beta_eastness": 0.15,
            "activity_beta_season": 0.30,
            "activity_beta_hour": 0.65,
            "alpha_foraging": -0.10,
            "beta_foraging_precip": -0.20,
            "beta_foraging_eastness": 0.65,
            "beta_foraging_season": 0.25,
            "beta_foraging_hour": -0.70,
        }
    )
    obs_b["opportunistic"].update(
        {
            "gamma_precip": 0.10,
            "gamma_season": 0.55,
            "gamma_hour": -0.05,
            "detection_intercept": -0.70,
        }
    )

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"].update(
        {
            "beta_precip": 0.20,
            "activity_intercept": -0.75,
            "activity_beta_precip": 0.25,
            "activity_beta_eastness": 0.60,
            "activity_beta_season": 0.75,
            "activity_beta_hour": 0.20,
            "alpha_foraging": 0.50,
            "beta_foraging_precip": -0.70,
            "beta_foraging_eastness": 0.20,
            "beta_foraging_season": 0.70,
            "beta_foraging_hour": -0.20,
        }
    )
    obs_c["opportunistic"].update(
        {
            "gamma_precip": 0.60,
            "gamma_season": 0.10,
            "gamma_hour": -0.50,
            "detection_intercept": 0.35,
        }
    )

    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )


def v04_r2_unknown_detection_anchors(fixture: V04R2Fixture):
    if fixture.profile != "unknown_detection":
        raise ValueError("R2 refusal anchors require unknown-detection fixture")

    truth_theta, truth_obs = _copy_state(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"]["activity_intercept"] = 0.20
    obs_b["annotated"]["detection_intercept"] = -0.30

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"]["activity_intercept"] = -0.90
    obs_c["annotated"]["detection_intercept"] = 0.90

    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )
