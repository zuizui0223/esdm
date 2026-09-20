"""Frozen v0.4 semi-synthetic state/activity validation fixture.

This module defines geometry, known truth, calibration exposure, and identification
anchors only. It does not inspect fitted outcomes and it does not make scientific claims.
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
class V04StateActivityFixture:
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
    training = tuple(
        getter(station)
        for station in stations
        if station.station_id in train_set
    )
    mean = statistics.fmean(training)
    sd = statistics.pstdev(training)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("training covariate must have positive finite variation")
    return {
        station.station_id: (getter(station) - mean) / sd
        for station in stations
    }


def _nearest_rank_quantiles(
    spaces: tuple[str, ...],
    values: Mapping[str, float],
    *,
    count: int,
) -> tuple[str, ...]:
    ordered = tuple(sorted(spaces, key=lambda space: (values[space], space)))
    if len(ordered) < count:
        raise ValueError("not enough training spaces for frozen rank quantiles")
    ranks = []
    for k in range(count):
        raw = k * (len(ordered) - 1) / (count - 1)
        ranks.append(int(math.floor(raw + 0.5)))
    selected = tuple(ordered[index] for index in ranks)
    if len(set(selected)) != count:
        raise ValueError("frozen rank quantiles did not yield unique stations")
    return selected


def _positive_calibration_spaces(
    train_spaces: tuple[str, ...],
    eastness_by_space: Mapping[str, float],
) -> tuple[str, ...]:
    return _nearest_rank_quantiles(
        train_spaces,
        eastness_by_space,
        count=18,
    )


def _sparse_calibration_spaces(
    train_spaces: tuple[str, ...],
    precip_by_space: Mapping[str, float],
    eastness_by_space: Mapping[str, float],
) -> tuple[str, ...]:
    ordered = sorted(
        train_spaces,
        key=lambda space: (
            precip_by_space[space] ** 2 + eastness_by_space[space] ** 2,
            space,
        ),
    )
    if len(ordered) < 6:
        raise ValueError("sparse v0.4 profile requires at least six training stations")
    return tuple(ordered[:6])


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
        raise ValueError("v0.4 fixture requires non-empty train and east held-out spaces")

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
    covariates = {
        key: {
            "precip_z_train": float(precip[key[0]]),
            "lat_z_train": float(latitude[key[0]]),
            "eastness_z_train": float(eastness[key[0]]),
        }
        for key in grid.keys
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


def _state_process() -> LinearState:
    states = StateSpace(("resting", "foraging"))
    return LinearState(
        state_space=states,
        reference_state="resting",
        covariates=("precip_z_train", "eastness_z_train"),
        intercept_parameters={
            "foraging": "alpha_foraging",
        },
        coefficient_parameters={
            "foraging": {
                "precip_z_train": "beta_foraging_precip",
                "eastness_z_train": "beta_foraging_eastness",
            }
        },
    )


def _known_activity() -> LinearActivity:
    return LinearActivity(
        covariates=("precip_z_train", "eastness_z_train"),
        intercept_parameter="activity_intercept",
        coefficient_parameters={
            "precip_z_train": "activity_beta_precip",
            "eastness_z_train": "activity_beta_eastness",
        },
    )


def _truth(*, intercept_only_activity: bool) -> dict[str, dict[str, float]]:
    values = {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "activity_intercept": -0.35,
        "alpha_foraging": 0.20,
        "beta_foraging_precip": -0.50,
        "beta_foraging_eastness": 0.45,
    }
    if not intercept_only_activity:
        values.update(
            {
                "activity_beta_precip": 0.55,
                "activity_beta_eastness": 0.40,
            }
        )
    return {"sp": values}


def _streams(
    grid: Grid,
    calibration_spaces: tuple[str, ...],
    heldout_spaces: tuple[str, ...],
    *,
    unknown_detection: bool,
):
    presence = PresenceOnly(
        name="presence",
        effort=EffortField({key: 5.0 for key in grid.keys}),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    exposed_spaces = set(calibration_spaces) | set(heldout_spaces)
    detection = (
        LogitDetection("detection_intercept")
        if unknown_detection
        else KnownDetection(probability=0.85)
    )
    annotated = StateAnnotatedCount(
        name="annotated",
        state_space=StateSpace(("resting", "foraging")),
        effort=EffortField(
            {
                key: 8.0
                for key in grid.keys
                if key[0] in exposed_spaces
            }
        ),
        detection=detection,
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )
    return presence, annotated


def build_v04_state_activity_fixture(
    source_csv_text: str,
    *,
    profile: str = "positive",
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V04StateActivityFixture:
    """Build the frozen known-detection v0.4 fixture."""

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
        _positive_calibration_spaces(train_spaces, eastness)
        if normalized == "positive"
        else _sparse_calibration_spaces(train_spaces, precip, eastness)
    )
    processes = (
        _suitability(),
        _known_activity(),
        _state_process(),
    )
    streams = _streams(
        grid,
        calibration_spaces,
        heldout_spaces,
        unknown_detection=False,
    )
    model = Model(
        domain=grid,
        species={"sp": processes},
        streams=streams,
    )
    model.check_design()

    return V04StateActivityFixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        calibration_spaces=calibration_spaces,
        profile=normalized,
        generating_theta=_truth(intercept_only_activity=False),
        generating_theta_obs={
            "presence": {},
            "annotated": {},
        },
        manifest=manifest,
    )


def build_v04_unknown_detection_fixture(
    source_csv_text: str,
    *,
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V04StateActivityFixture:
    """Build the frozen unknown-detection structural-refusal fixture."""

    (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        _precip,
        eastness,
    ) = _base_geometry(source_csv_text, manifest)
    calibration_spaces = _positive_calibration_spaces(train_spaces, eastness)
    processes = (
        _suitability(),
        LinearActivity(
            covariates=(),
            intercept_parameter="activity_intercept",
            coefficient_parameters={},
        ),
        _state_process(),
    )
    streams = _streams(
        grid,
        calibration_spaces,
        heldout_spaces,
        unknown_detection=True,
    )
    model = Model(
        domain=grid,
        species={"sp": processes},
        streams=streams,
    )
    model.check_design()
    return V04StateActivityFixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        calibration_spaces=calibration_spaces,
        profile="unknown_detection",
        generating_theta=_truth(intercept_only_activity=True),
        generating_theta_obs={
            "presence": {},
            "annotated": {"detection_intercept": 0.40},
        },
        manifest=manifest,
    )


def _copy_theta(fixture: V04StateActivityFixture):
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


def v04_identification_anchors(
    fixture: V04StateActivityFixture,
):
    """Return the three frozen known-detection identification anchors."""

    if fixture.profile not in {"positive", "sparse"}:
        raise ValueError("known-detection anchors require positive or sparse fixture")
    truth_theta, truth_obs = _copy_theta(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"].update(
        {
            "activity_intercept": -0.10,
            "activity_beta_precip": 0.75,
            "activity_beta_eastness": 0.20,
            "alpha_foraging": -0.10,
            "beta_foraging_precip": -0.25,
            "beta_foraging_eastness": 0.70,
        }
    )

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"].update(
        {
            "activity_intercept": -0.70,
            "activity_beta_precip": 0.30,
            "activity_beta_eastness": 0.65,
            "alpha_foraging": 0.50,
            "beta_foraging_precip": -0.75,
            "beta_foraging_eastness": 0.20,
        }
    )
    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )


def v04_unknown_detection_anchors(
    fixture: V04StateActivityFixture,
):
    """Return the three frozen activity/detection refusal anchors."""

    if fixture.profile != "unknown_detection":
        raise ValueError("unknown-detection anchors require unknown-detection fixture")
    truth_theta, truth_obs = _copy_theta(fixture)

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
