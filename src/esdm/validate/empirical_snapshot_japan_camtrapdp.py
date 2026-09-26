"""Frozen real-data adapter for the Snapshot Japan 2023 Camtrap DP R5b endpoint."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from types import MappingProxyType
import zipfile

from esdm.domain import Grid, StateSpace
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    PresenceOnly,
    StateAnnotatedCount,
    StateCompositionCount,
)
from esdm.process import LinearActivity, LinearState, LinearSuitability
from esdm.process.base import PriorSpec


EAST_THRESHOLD_LONGITUDE = 140.25698549999998
FOCAL_SCIENTIFIC_NAME = "Cervus nippon"
STATES = StateSpace(("solitary", "group"))
HOUR_BINS = ((0, 5, 3), (6, 11, 9), (12, 17, 15), (18, 23, 21))
STREAM_SALT = "snapshot-japan-camtrapdp-r5b-stream-v1|"
REQUIRED_MEMBERS = frozenset({"deployments.csv", "observations.csv"})


@dataclass(frozen=True, slots=True)
class MaskedLogLinearEffort:
    """Unknown seasonal effort over a frozen structural exposure mask."""

    exposed_keys: frozenset[tuple[str, int, int]]
    covariate: str
    coefficient_parameter: str
    baseline: float = 1.0

    def __post_init__(self) -> None:
        covariate = str(self.covariate).strip()
        parameter = str(self.coefficient_parameter).strip()
        baseline = float(self.baseline)
        if not covariate or not parameter:
            raise ValueError("masked effort names must be non-empty")
        if not math.isfinite(baseline) or baseline <= 0.0:
            raise ValueError("masked effort baseline must be finite and positive")
        object.__setattr__(
            self,
            "exposed_keys",
            frozenset(
                (str(key[0]), int(key[1]), int(key[2]))
                for key in self.exposed_keys
            ),
        )
        object.__setattr__(self, "covariate", covariate)
        object.__setattr__(self, "coefficient_parameter", parameter)
        object.__setattr__(self, "baseline", baseline)

    @property
    def requires(self) -> frozenset[str]:
        return frozenset({self.covariate})

    def priors(self):
        return {
            self.coefficient_parameter: PriorSpec(
                "Normal", {"loc": 0.0, "scale": 1.0}
            )
        }

    def at(self, key, *, theta, covariates, exp_fn=math.exp):
        normalized = (str(key[0]), int(key[1]), int(key[2]))
        if normalized not in self.exposed_keys:
            return 0.0
        if self.coefficient_parameter not in theta:
            raise KeyError(
                f"missing observation-effort parameter {self.coefficient_parameter!r}"
            )
        if normalized not in covariates or self.covariate not in covariates[normalized]:
            raise KeyError(
                f"missing observation-effort covariate {self.covariate!r} for {normalized!r}"
            )
        return self.baseline * exp_fn(
            theta[self.coefficient_parameter]
            * covariates[normalized][self.covariate]
        )

    def array(self, keys, *, theta, covariates, array_module):
        if self.coefficient_parameter not in theta:
            raise KeyError(
                f"missing observation-effort parameter {self.coefficient_parameter!r}"
            )
        values = []
        for key in keys:
            normalized = (str(key[0]), int(key[1]), int(key[2]))
            if normalized not in self.exposed_keys:
                values.append(0.0)
                continue
            if normalized not in covariates or self.covariate not in covariates[normalized]:
                raise KeyError(
                    f"missing observation-effort covariate {self.covariate!r} "
                    f"for {normalized!r}"
                )
            values.append(
                self.baseline
                * array_module.exp(
                    theta[self.coefficient_parameter]
                    * covariates[normalized][self.covariate]
                )
            )
        return array_module.asarray(values)

    def structural_exposure_mask(self, keys):
        return tuple(
            (str(key[0]), int(key[1]), int(key[2])) in self.exposed_keys
            for key in keys
        )


@dataclass(frozen=True, slots=True)
class SnapshotJapanEmpiricalFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    data: Mapping[str, object]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    stream_by_space: Mapping[str, str]
    source_sha256: str
    source_md5: str
    climate_sha256: str
    diagnostics: Mapping[str, object]

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
            "stream_by_space",
            MappingProxyType(dict(self.stream_by_space)),
        )
        object.__setattr__(
            self,
            "diagnostics",
            MappingProxyType(dict(self.diagnostics)),
        )


def _parse_iso(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        raise ValueError("timestamp is empty")
    result = datetime.fromisoformat(text)
    if result.tzinfo is None:
        raise ValueError("Camtrap DP timestamps must include timezone")
    return result


def _representative_doy(value: datetime) -> int:
    iso = value.isocalendar()
    thursday = datetime.fromisocalendar(iso.year, iso.week, 4).date()
    return int(thursday.timetuple().tm_yday)


def _hour_bin(hour: int) -> int:
    value = int(hour)
    for start, end, representative in HOUR_BINS:
        if start <= value <= end:
            return representative
    raise ValueError(f"hour outside 0..23: {hour!r}")


def _role(deployment_id: str) -> str:
    token = (STREAM_SALT + str(deployment_id)).encode("utf-8")
    byte = hashlib.sha256(token).digest()[0]
    if byte <= 63:
        return "opportunistic_presence"
    if byte <= 127:
        return "calibrated_presence"
    if byte <= 207:
        return "state_annotated"
    return "state_calibration"


def _read_csv(payload: bytes):
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    return tuple(reader.fieldnames or ()), list(reader)


def _required(columns, names, *, label: str):
    missing = [name for name in names if name not in set(columns)]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _climate_lookup(climate_payload):
    if climate_payload.get("status") != "CLIMATE_QUALIFIED":
        raise ValueError("climate payload is not qualified")
    rows = tuple(climate_payload.get("camera_climate", ()))
    if len(rows) != 90:
        raise ValueError("climate payload must contain 90 cameras")
    return rows


def _match_climate(latitude: float, longitude: float, climate_rows):
    matches = [
        row
        for row in climate_rows
        if abs(float(row["latitude"]) - latitude) <= 1e-5
        and abs(float(row["longitude"]) - longitude) <= 1e-5
    ]
    if len(matches) != 1:
        raise ValueError(
            f"deployment coordinate ({latitude}, {longitude}) does not map "
            f"uniquely to frozen response-blind climate geometry"
        )
    return matches[0]


def _active_effort_by_context(start: datetime, end: datetime):
    if end <= start:
        raise ValueError("deploymentEnd must be after deploymentStart")
    output: dict[tuple[int, int], float] = {}
    cursor_date = start.date()
    end_date = end.date()
    while cursor_date <= end_date:
        for start_hour, _end_hour, representative in HOUR_BINS:
            bin_start = datetime.combine(
                cursor_date,
                datetime.min.time(),
                tzinfo=start.tzinfo,
            ) + timedelta(hours=start_hour)
            bin_end = bin_start + timedelta(hours=6)
            overlap_start = max(start, bin_start)
            overlap_end = min(end, bin_end)
            seconds = max(0.0, (overlap_end - overlap_start).total_seconds())
            if seconds > 0.0:
                midpoint = bin_start + timedelta(hours=3)
                key = (_representative_doy(midpoint), representative)
                output[key] = output.get(key, 0.0) + seconds / 86400.0
        cursor_date += timedelta(days=1)
    return output


def _processes():
    return (
        LinearSuitability(
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
        ),
        LinearActivity(
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
        ),
        LinearState(
            state_space=STATES,
            reference_state="solitary",
            covariates=(
                "precip_z_train",
                "eastness_z_train",
                "season_sin",
                "diurnal_sin",
            ),
            intercept_parameters={"group": "alpha_group"},
            coefficient_parameters={
                "group": {
                    "precip_z_train": "beta_group_precip",
                    "eastness_z_train": "beta_group_eastness",
                    "season_sin": "beta_group_season",
                    "diurnal_sin": "beta_group_diurnal",
                }
            },
        ),
    )


def build_snapshot_japan_empirical_fixture(
    *,
    camtrapdp_zip: bytes,
    climate_payload: Mapping[str, object],
    expected_md5: str,
    expected_deployment_count: int = 90,
    minimum_role_count: int = 8,
    minimum_training_state_count: int = 10,
    minimum_calibration_state_count: int = 10,
    minimum_heldout_state_count: int = 5,
) -> SnapshotJapanEmpiricalFixture:
    """Parse the frozen Camtrap DP response and construct the unchanged R5b graph."""

    source_md5 = hashlib.md5(camtrapdp_zip).hexdigest()  # noqa: S324 provenance only
    if source_md5 != str(expected_md5):
        raise ValueError(f"Camtrap DP MD5 drift: {source_md5}")
    source_sha256 = hashlib.sha256(camtrapdp_zip).hexdigest()

    with zipfile.ZipFile(io.BytesIO(camtrapdp_zip)) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_MEMBERS - names
        if missing:
            raise ValueError(f"Camtrap DP missing members: {sorted(missing)}")
        deployment_columns, deployment_rows = _read_csv(
            archive.read("deployments.csv")
        )
        observation_columns, observation_rows = _read_csv(
            archive.read("observations.csv")
        )

    _required(
        deployment_columns,
        (
            "deploymentID",
            "latitude",
            "longitude",
            "deploymentStart",
            "deploymentEnd",
        ),
        label="deployments.csv",
    )
    _required(
        observation_columns,
        (
            "observationID",
            "deploymentID",
            "eventID",
            "eventStart",
            "observationLevel",
            "observationType",
            "scientificName",
            "count",
        ),
        label="observations.csv",
    )
    if len(deployment_rows) != int(expected_deployment_count):
        raise ValueError(
            f"Camtrap DP deployment count drift: {len(deployment_rows)}"
        )

    climate_rows = _climate_lookup(dict(climate_payload))
    deployments = {}
    for index, row in enumerate(deployment_rows):
        deployment_id = str(row["deploymentID"]).strip()
        if not deployment_id or deployment_id in deployments:
            raise ValueError(
                f"deploymentID must be unique and non-empty at row {index}"
            )
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        start = _parse_iso(row["deploymentStart"])
        end = _parse_iso(row["deploymentEnd"])
        climate = _match_climate(latitude, longitude, climate_rows)
        partition = (
            "training"
            if longitude < EAST_THRESHOLD_LONGITUDE
            else "heldout"
            if longitude > EAST_THRESHOLD_LONGITUDE
            else "boundary"
        )
        if partition == "boundary":
            raise ValueError("deployment lies exactly on frozen east boundary")
        role = _role(deployment_id) if partition == "training" else "heldout_state_annotated"
        deployments[deployment_id] = {
            "latitude": latitude,
            "longitude": longitude,
            "start": start,
            "end": end,
            "partition": partition,
            "role": role,
            "precip_z_train": float(climate["precip_z_train"]),
            "effort": _active_effort_by_context(start, end),
        }

    train_spaces = tuple(sorted(
        deployment_id
        for deployment_id, row in deployments.items()
        if row["partition"] == "training"
    ))
    heldout_spaces = tuple(sorted(
        deployment_id
        for deployment_id, row in deployments.items()
        if row["partition"] == "heldout"
    ))
    if len(train_spaces) != 70 or len(heldout_spaces) != 20:
        raise ValueError(
            f"frozen east split drift: {len(train_spaces)} training / "
            f"{len(heldout_spaces)} heldout"
        )
    if min(deployments[s]["longitude"] for s in heldout_spaces) <= max(
        deployments[s]["longitude"] for s in train_spaces
    ):
        raise ValueError("Camtrap DP east holdout is not strictly extrapolative")

    role_counts = {
        name: sum(
            deployments[space]["role"] == name
            for space in train_spaces
        )
        for name in (
            "opportunistic_presence",
            "calibrated_presence",
            "state_annotated",
            "state_calibration",
        )
    }
    bad = [
        name for name, count in role_counts.items()
        if count < int(minimum_role_count)
    ]
    if bad:
        raise ValueError(f"training role below frozen minimum: {bad}")

    training_latitudes = [deployments[s]["latitude"] for s in train_spaces]
    training_longitudes = [deployments[s]["longitude"] for s in train_spaces]
    lat_mean = math.fsum(training_latitudes) / len(training_latitudes)
    lon_mean = math.fsum(training_longitudes) / len(training_longitudes)
    lat_sd = math.sqrt(
        math.fsum((value - lat_mean) ** 2 for value in training_latitudes)
        / len(training_latitudes)
    )
    lon_sd = math.sqrt(
        math.fsum((value - lon_mean) ** 2 for value in training_longitudes)
        / len(training_longitudes)
    )
    if lat_sd <= 0.0 or lon_sd <= 0.0:
        raise ValueError("training latitude/eastness lacks positive variation")

    doy_values = sorted({
        doy
        for meta in deployments.values()
        for doy, _hour in meta["effort"]
    })
    hour_values = tuple(bin_[2] for bin_ in HOUR_BINS)
    if not doy_values:
        raise ValueError("deployment effort produced no temporal contexts")
    grid = Grid(
        space=tuple(sorted(deployments)),
        doy=tuple(doy_values),
        hour=hour_values,
    )

    covariates = {}
    for key in grid.keys:
        space, doy, hour = key
        meta = deployments[space]
        season_phase = 2.0 * math.pi * (float(doy) - 15.0) / 365.0
        diurnal_phase = 2.0 * math.pi * float(hour) / 24.0
        covariates[key] = {
            "precip_z_train": meta["precip_z_train"],
            "lat_z_train": (meta["latitude"] - lat_mean) / lat_sd,
            "eastness_z_train": (meta["longitude"] - lon_mean) / lon_sd,
            "season_sin": math.sin(season_phase),
            "season_cos": math.cos(season_phase),
            "diurnal_sin": math.sin(diurnal_phase),
            "diurnal_cos": math.cos(diurnal_phase),
        }

    opportunistic_exposed = frozenset(
        (space, doy, hour)
        for space in train_spaces
        if deployments[space]["role"] == "opportunistic_presence"
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    )
    calibrated_effort = {
        (space, doy, hour): effort
        for space in train_spaces
        if deployments[space]["role"] == "calibrated_presence"
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    }
    annotated_effort = {
        (space, doy, hour): effort
        for space in tuple(train_spaces) + tuple(heldout_spaces)
        if deployments[space]["role"] in {
            "state_annotated",
            "heldout_state_annotated",
        }
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    }

    presence_counts = {
        "opportunistic_presence": {},
        "calibrated_presence": {},
    }
    state_counts = {
        "state_annotated": {
            "solitary": {},
            "group": {},
        },
        "state_calibration": {
            "solitary": {},
            "group": {},
        },
    }
    focal_events: dict[tuple[str, str], dict[str, object]] = {}
    for index, row in enumerate(observation_rows):
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue
        if str(row.get("scientificName", "")).strip() != FOCAL_SCIENTIFIC_NAME:
            continue
        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        if deployment_id not in deployments or not event_id:
            raise ValueError(
                f"focal event at observation row {index} lacks frozen deployment/event identity"
            )
        event_start = _parse_iso(row.get("eventStart", ""))
        meta = deployments[deployment_id]
        if not (meta["start"] <= event_start <= meta["end"]):
            raise ValueError(
                f"focal event {event_id!r} lies outside deployment interval"
            )
        key = (deployment_id, event_id)
        record = focal_events.setdefault(
            key,
            {
                "deployment_id": deployment_id,
                "event_id": event_id,
                "event_start": event_start,
                "counts": [],
            },
        )
        if record["event_start"] != event_start:
            raise ValueError(
                f"focal event {event_id!r} has inconsistent eventStart"
            )
        count_text = str(row.get("count", "")).strip()
        if not count_text:
            record["counts"].append(None)
        else:
            count = int(float(count_text))
            if count < 1:
                raise ValueError("focal event count must be positive")
            record["counts"].append(count)

    labelled_events = []
    for event in focal_events.values():
        deployment_id = event["deployment_id"]
        meta = deployments[deployment_id]
        start = event["event_start"]
        context = (
            deployment_id,
            _representative_doy(start),
            _hour_bin(start.hour),
        )
        if context not in set(grid.keys):
            raise ValueError("focal event maps outside frozen model domain")
        role = meta["role"]
        if role == "opportunistic_presence":
            presence_counts["opportunistic_presence"][context] = (
                presence_counts["opportunistic_presence"].get(context, 0) + 1
            )
        elif role == "calibrated_presence":
            presence_counts["calibrated_presence"][context] = (
                presence_counts["calibrated_presence"].get(context, 0) + 1
            )

        counts = tuple(event["counts"])
        if any(value is None for value in counts):
            if role in {
                "state_annotated",
                "state_calibration",
                "heldout_state_annotated",
            }:
                raise ValueError(
                    "focal event in a frozen state-information deployment has missing count"
                )
            continue
        group_size = sum(int(value) for value in counts)
        state = "solitary" if group_size == 1 else "group"
        labelled_events.append((deployment_id, context, state))
        if role in {"state_annotated", "heldout_state_annotated"}:
            block = state_counts["state_annotated"][state]
            block[context] = block.get(context, 0) + 1
        elif role == "state_calibration":
            block = state_counts["state_calibration"][state]
            block[context] = block.get(context, 0) + 1

    state_calibration_effort = {}
    for state in STATES.states:
        for context, count in state_counts["state_calibration"][state].items():
            state_calibration_effort[context] = (
                state_calibration_effort.get(context, 0) + int(count)
            )

    streams = (
        PresenceOnly(
            name="presence_opportunistic",
            effort=MaskedLogLinearEffort(
                exposed_keys=opportunistic_exposed,
                covariate="season_sin",
                coefficient_parameter="gamma_presence_season",
            ),
            detection_probability=1.0,
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        ),
        PresenceOnly(
            name="presence_calibrated",
            effort=EffortField(calibrated_effort),
            detection_probability=1.0,
            informs=frozenset({"suitability"}),
            targets=frozenset({"sp"}),
        ),
        StateAnnotatedCount(
            name="annotated",
            state_space=STATES,
            effort=EffortField(annotated_effort),
            detection=KnownDetection(probability=1.0),
            informs=frozenset({"activity", "state"}),
            targets=frozenset({"sp"}),
        ),
        StateCompositionCount(
            name="state_calibration",
            state_space=STATES,
            effort=EffortField(state_calibration_effort),
            informs=frozenset({"state"}),
            targets=frozenset({"sp"}),
        ),
    )
    model = Model(
        domain=grid,
        species={"sp": _processes()},
        streams=streams,
    )
    model.check_design()

    all_keys = tuple(grid.keys)
    data = {
        "presence_opportunistic": {
            "sp": {
                key: int(presence_counts["opportunistic_presence"].get(key, 0))
                for key in all_keys
            }
        },
        "presence_calibrated": {
            "sp": {
                key: int(presence_counts["calibrated_presence"].get(key, 0))
                for key in all_keys
            }
        },
        "annotated": {
            "sp": {
                state: {
                    key: int(state_counts["state_annotated"][state].get(key, 0))
                    for key in all_keys
                }
                for state in STATES.states
            }
        },
        "state_calibration": {
            "sp": {
                state: {
                    key: int(state_counts["state_calibration"][state].get(key, 0))
                    for key in all_keys
                }
                for state in STATES.states
            }
        },
    }

    def _state_total(role_name, state, spaces):
        space_set = set(spaces)
        return sum(
            count
            for key, count in state_counts[role_name][state].items()
            if key[0] in space_set
        )

    train_annotated_spaces = tuple(
        space for space in train_spaces
        if deployments[space]["role"] == "state_annotated"
    )
    calibration_spaces = tuple(
        space for space in train_spaces
        if deployments[space]["role"] == "state_calibration"
    )
    state_diagnostics = {
        "training_state_annotated": {
            state: _state_total("state_annotated", state, train_annotated_spaces)
            for state in STATES.states
        },
        "state_calibration": {
            state: _state_total("state_calibration", state, calibration_spaces)
            for state in STATES.states
        },
        "heldout_state_annotated": {
            state: _state_total("state_annotated", state, heldout_spaces)
            for state in STATES.states
        },
    }
    for state in STATES.states:
        if state_diagnostics["training_state_annotated"][state] < int(
            minimum_training_state_count
        ):
            raise ValueError(
                f"training annotated {state} below frozen minimum"
            )
        if state_diagnostics["state_calibration"][state] < int(
            minimum_calibration_state_count
        ):
            raise ValueError(
                f"state calibration {state} below frozen minimum"
            )
        if state_diagnostics["heldout_state_annotated"][state] < int(
            minimum_heldout_state_count
        ):
            raise ValueError(
                f"heldout annotated {state} below frozen minimum"
            )

    event_totals = {
        name: sum(values["sp"].values())
        for name, values in data.items()
        if name.startswith("presence_")
    }
    if event_totals["presence_opportunistic"] < 10:
        raise ValueError("opportunistic focal events below frozen minimum")
    if event_totals["presence_calibrated"] < 10:
        raise ValueError("calibrated focal events below frozen minimum")

    diagnostics = {
        "deployment_count": len(deployments),
        "training_count": len(train_spaces),
        "heldout_count": len(heldout_spaces),
        "role_counts": role_counts,
        "focal_event_count": len(focal_events),
        "labelled_focal_event_count": len(labelled_events),
        "presence_event_totals": event_totals,
        "state_counts": state_diagnostics,
    }
    return SnapshotJapanEmpiricalFixture(
        model=model,
        covariates=covariates,
        data=data,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        stream_by_space={
            space: deployments[space]["role"]
            for space in deployments
        },
        source_sha256=source_sha256,
        source_md5=source_md5,
        climate_sha256=str(climate_payload["camera_climate_sha256"]),
        diagnostics=diagnostics,
    )
