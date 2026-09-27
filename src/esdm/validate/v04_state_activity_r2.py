"""Frozen v0.4 R2 validation fixture.

R2 strengthens the first v0.4 gate by retaining unknown observation-process parameters,
partial calibrated streams, and explicit temporal ecological/observation covariates.
This module contains geometry/truth/anchor definitions only and never inspects outcomes.
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
    LogLinearEffort,
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
    presence_calibration_spaces: tuple[str, ...]
    annotation_calibration_spaces: tuple[str, ...]
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
                    key: MappingProxyType(dict(values))
                    for key, values in self.generating_theta.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "generating_theta_obs",
            MappingProxyType(
                {
                    key: MappingProxyType(dict(values))
                    for key, values in self.generating_theta_obs.items()
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


def _rank_quantiles(
    spaces: tuple[str, ...],
    values: Mapping[str, float],
    *,
    count: int,
) -> tuple[str, ...]:
    ordered = tuple(sorted(spaces, key=lambda space: (values[space], space)))
    if len(ordered) < count:
        raise ValueError("insufficient training spaces for frozen calibration profile")
    indices = []
    for k in range(count):
        raw = k * (len(ordered) - 1) / (count - 1)
        indices.append(int(math.floor(raw + 0.5)))
    selected = tuple(ordered[index] for index in indices)
    if len(set(selected)) != count:
        raise ValueError("rank-quantile calibration selection was not unique")
    return selected


def _geometry(
    source_csv_text: str,
    manifest: V031SemiSyntheticManifest,
):
    stations = parse_station_csv(source_csv_text, rows=manifest.station_rows)
    spaces = tuple(station.station_id for station in stations)
    blocks = {
        station.station_id: _block(station.longitude)
        for station in stations
    }
    train_spaces = tuple(space for space in spaces if blocks[space] != "east")
    heldout_spaces = tuple(space for space in spaces if blocks[space] == "east")
    if not train_spaces or not heldout_spaces:
        raise ValueError("R2 requires non-empty training and east held-out blocks")

    precip = _training_standardize(
        stations, train_spaces, lambda station: station.average_precip
    )
    latitude = _training_standardize(
        stations, train_spaces, lambda station: station.latitude
    )
    eastness = _training_standardize(
        stations, train_spaces, lambda station: station.longitude
    )
    if min(eastness[space] for space in heldout_spaces) <= max(
        eastness[space] for space in train_spaces
    ):
        raise ValueError("east held-out block is not outside training eastness range")

    grid = Grid(
        space=spaces,
        doy=manifest.doy_bins,
        hour=manifest.hour_bins,
    )
    covariates = {}
    for key in grid.keys:
        space, doy, hour = key
        phase_doy = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
        phase_hour = 2.0 * math.pi * float(hour) / 24.0
        covariates[key] = {
            "precip_z_train": float(precip[space]),
            "lat_z_train": float(latitude[space]),
            "eastness_z_train": float(eastness[space]),
            "season_sin": math.sin(phase_doy),
            "season_cos": math.cos(phase_doy),
            "diurnal_sin": math.sin(phase_hour),
            "diurnal_cos": math.cos(phase_hour),
        }

    return (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        eastness,
    )


def _state_space() -> StateSpace:
    return StateSpace(("resting", "foraging"))


def _suitability() -> LinearSuitability:
    return LinearSuitability(
        covariates=(
            "precip_z_train",
            "lat_z_train",
            "eastness_z_train",
            "season_sin",
        ),
        intercept_parameter="intercept",
        coefficient_parameters={
            "precip_z_train": "beta_precip",
            "lat_z_train": "beta_lat",
            "eastness_z_train": "beta_eastness",
            "season_sin": "beta_season",
        },
    )


def _activity(*, intercept_only: bool) -> LinearActivity:
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
            "season_cos",
            "diurnal_cos",
        ),
        intercept_parameter="activity_intercept",
        coefficient_parameters={
            "precip_z_train": "activity_beta_precip",
            "eastness_z_train": "activity_beta_eastness",
            "season_cos": "activity_beta_season",
            "diurnal_cos": "activity_beta_diurnal",
        },
    )


def _state() -> LinearState:
    states = _state_space()
    return LinearState(
        state_space=states,
        reference_state="resting",
        covariates=(
            "precip_z_train",
            "eastness_z_train",
            "season_sin",
            "diurnal_sin",
        ),
        intercept_parameters={"foraging": "alpha_foraging"},
        coefficient_parameters={
            "foraging": {
                "precip_z_train": "beta_foraging_precip",
                "eastness_z_train": "beta_foraging_eastness",
                "season_sin": "beta_foraging_season",
                "diurnal_sin": "beta_foraging_diurnal",
            }
        },
    )


def _intensity_theta():
    return {
        "sp": {
            "intercept": -2.0,
            "beta_precip": 0.45,
            "beta_lat": -0.20,
            "beta_eastness": 0.35,
            "beta_season": 0.30,
        }
    }


def _theta(*, intercept_only_activity: bool):
    values = {
        "intercept": -2.0,
        "beta_precip": 0.45,
        "beta_lat": -0.20,
        "beta_eastness": 0.35,
        "beta_season": 0.30,
        "activity_intercept": -0.35,
        "alpha_foraging": 0.20,
        "beta_foraging_precip": -0.35,
        "beta_foraging_eastness": 0.40,
        "beta_foraging_season": -0.50,
        "beta_foraging_diurnal": 0.55,
    }
    if not intercept_only_activity:
        values.update(
            {
                "activity_beta_precip": 0.40,
                "activity_beta_eastness": 0.30,
                "activity_beta_season": 0.50,
                "activity_beta_diurnal": 0.45,
            }
        )
    return {"sp": values}


def _streams(
    grid: Grid,
    presence_calibration_spaces: tuple[str, ...],
    annotation_calibration_spaces: tuple[str, ...],
    *,
    include_presence_calibrated: bool,
    include_annotation_calibrated: bool,
):
    presence_opp = PresenceOnly(
        name="presence_opportunistic",
        effort=LogLinearEffort(
            baseline=4.0,
            covariate="season_sin",
            coefficient_parameter="gamma_presence_season",
        ),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )

    presence_set = set(presence_calibration_spaces)
    presence_cal = PresenceOnly(
        name="presence_calibrated",
        effort=EffortField(
            {
                key: 3.0
                for key in grid.keys
                if key[0] in presence_set
            }
        ),
        detection_probability=1.0,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )

    annotated_opp = StateAnnotatedCount(
        name="annotated_opportunistic",
        state_space=_state_space(),
        effort=LogLinearEffort(
            baseline=6.0,
            covariate="diurnal_cos",
            coefficient_parameter="gamma_annotation_diurnal",
        ),
        detection=LogitDetection("detection_intercept"),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )

    annotation_set = set(annotation_calibration_spaces)
    annotated_cal = StateAnnotatedCount(
        name="annotated_calibrated",
        state_space=_state_space(),
        effort=EffortField(
            {
                key: 5.0
                for key in grid.keys
                if key[0] in annotation_set
            }
        ),
        detection=KnownDetection(probability=0.85),
        informs=frozenset({"activity", "state"}),
        targets=frozenset({"sp"}),
    )

    output = [presence_opp]
    if include_presence_calibrated:
        output.append(presence_cal)
    output.append(annotated_opp)
    if include_annotation_calibrated:
        output.append(annotated_cal)
    return tuple(output)


def _theta_obs(streams) -> dict[str, dict[str, float]]:
    truth = {}
    for stream in streams:
        if stream.name == "presence_opportunistic":
            truth[stream.name] = {"gamma_presence_season": 0.35}
        elif stream.name == "annotated_opportunistic":
            truth[stream.name] = {
                "gamma_annotation_diurnal": 0.30,
                "detection_intercept": 0.40,
            }
        else:
            truth[stream.name] = {}
    return truth


def build_v04_r2_fixture(
    source_csv_text: str,
    *,
    profile: str = "positive",
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V04R2Fixture:
    """Build a frozen R2 positive or refusal fixture."""

    normalized = str(profile).strip().lower()
    allowed = {
        "positive",
        "presence_effort_refusal",
        "activity_detection_refusal",
    }
    if normalized not in allowed:
        raise ValueError(f"profile must be one of {sorted(allowed)}")

    (
        stations,
        grid,
        covariates,
        train_spaces,
        heldout_spaces,
        eastness,
    ) = _geometry(source_csv_text, manifest)

    presence_calibration_spaces = _rank_quantiles(
        train_spaces,
        eastness,
        count=12,
    )
    annotation_calibration_spaces = _rank_quantiles(
        train_spaces,
        eastness,
        count=18,
    )

    if normalized == "presence_effort_refusal":
        all_streams = _streams(
            grid,
            presence_calibration_spaces,
            annotation_calibration_spaces,
            include_presence_calibrated=False,
            include_annotation_calibrated=False,
        )
        processes = (_suitability(),)
        streams = (all_streams[0],)
        generating_theta = _intensity_theta()
    else:
        intercept_only = normalized == "activity_detection_refusal"
        processes = (
            _suitability(),
            _activity(intercept_only=intercept_only),
            _state(),
        )
        streams = _streams(
            grid,
            presence_calibration_spaces,
            annotation_calibration_spaces,
            include_presence_calibrated=True,
            include_annotation_calibrated=not intercept_only,
        )
        generating_theta = _theta(intercept_only_activity=intercept_only)

    model = Model(
        domain=grid,
        species={"sp": processes},
        streams=streams,
    )
    model.check_design()

    return V04R2Fixture(
        model=model,
        stations=stations,
        covariates=covariates,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        presence_calibration_spaces=presence_calibration_spaces,
        annotation_calibration_spaces=annotation_calibration_spaces,
        profile=normalized,
        generating_theta=generating_theta,
        generating_theta_obs=_theta_obs(streams),
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


def v04_r2_positive_anchors(fixture: V04R2Fixture):
    """Return the three frozen R2 positive anchors."""

    if fixture.profile != "positive":
        raise ValueError("positive anchors require positive R2 fixture")
    truth_theta, truth_obs = _copy_state(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"].update(
        {
            "beta_season": 0.55,
            "activity_intercept": -0.05,
            "activity_beta_season": 0.25,
            "activity_beta_diurnal": 0.70,
            "activity_beta_eastness": 0.15,
            "beta_foraging_season": -0.25,
            "beta_foraging_diurnal": 0.75,
            "beta_foraging_eastness": 0.20,
        }
    )
    obs_b["presence_opportunistic"]["gamma_presence_season"] = 0.10
    obs_b["annotated_opportunistic"].update(
        {
            "gamma_annotation_diurnal": 0.10,
            "detection_intercept": -0.20,
        }
    )

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"].update(
        {
            "beta_season": 0.10,
            "activity_intercept": -0.70,
            "activity_beta_season": 0.75,
            "activity_beta_diurnal": 0.20,
            "activity_beta_eastness": 0.55,
            "beta_foraging_season": -0.75,
            "beta_foraging_diurnal": 0.25,
            "beta_foraging_eastness": 0.65,
        }
    )
    obs_c["presence_opportunistic"]["gamma_presence_season"] = 0.60
    obs_c["annotated_opportunistic"].update(
        {
            "gamma_annotation_diurnal": 0.60,
            "detection_intercept": 0.90,
        }
    )
    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )


def v04_r2_presence_refusal_anchors(fixture: V04R2Fixture):
    """Return the three frozen exact presence-effort refusal anchors."""

    if fixture.profile != "presence_effort_refusal":
        raise ValueError("presence refusal anchors require presence-effort refusal fixture")
    truth_theta, truth_obs = _copy_state(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"]["beta_season"] = 0.55
    obs_b["presence_opportunistic"]["gamma_presence_season"] = 0.10

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"]["beta_season"] = 0.10
    obs_c["presence_opportunistic"]["gamma_presence_season"] = 0.60

    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )


def v04_r2_detection_refusal_anchors(fixture: V04R2Fixture):
    """Return the three frozen R2 activity/detection refusal anchors."""

    if fixture.profile != "activity_detection_refusal":
        raise ValueError("detection refusal anchors require refusal fixture")
    truth_theta, truth_obs = _copy_state(fixture)

    theta_b = {name: dict(values) for name, values in truth_theta.items()}
    obs_b = {name: dict(values) for name, values in truth_obs.items()}
    theta_b["sp"]["activity_intercept"] = 0.20
    obs_b["annotated_opportunistic"]["detection_intercept"] = -0.30

    theta_c = {name: dict(values) for name, values in truth_theta.items()}
    obs_c = {name: dict(values) for name, values in truth_obs.items()}
    theta_c["sp"]["activity_intercept"] = -0.90
    obs_c["annotated_opportunistic"]["detection_intercept"] = 0.90

    return (
        (truth_theta, truth_obs),
        (theta_b, obs_b),
        (theta_c, obs_c),
    )
