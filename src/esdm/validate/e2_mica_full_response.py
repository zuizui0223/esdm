"""Frozen full-response adapter for the E2 MICA muskrat replication."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
from types import MappingProxyType
import zipfile

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import (
    EffortField,
    KnownDetection,
    PresenceOnly,
    StateAnnotatedCount,
    StateCompositionCount,
)

from .e2_mica_response_blind import qualify_e2_mica_archive
from .e2_mica_temporal_integrity import audit_e2_mica_temporal_integrity
from .e2_mica_worldclim import _canonical_sha256 as _climate_rows_sha256
from .empirical_snapshot_japan_camtrapdp import (
    HOUR_BINS,
    STATES,
    MaskedLogLinearEffort,
    _active_effort_by_context,
    _hour_bin,
    _parse_iso,
    _processes,
    _representative_doy,
)


FOCAL_SCIENTIFIC_NAME = "Ondatra zibethicus"
REQUIRED_MEMBERS = frozenset({"deployments.csv", "observations.csv"})
REQUIRED_OBSERVATION_COLUMNS = frozenset({
    "deploymentID",
    "eventID",
    "eventStart",
    "observationLevel",
    "observationType",
    "scientificName",
    "count",
})


@dataclass(frozen=True, slots=True)
class E2MicaEmpiricalFixture:
    model: Model
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    data: Mapping[str, object]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    stream_by_space: Mapping[str, str]
    source_sha256: str
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


def _find_unique_entry(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if PurePosixPath(name).name == basename and not name.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"archive must contain exactly one {basename!r}; observed {matches!r}"
        )
    return matches[0]


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assert_equal(label: str, observed, expected) -> None:
    if observed != expected:
        raise ValueError(
            f"E2 MICA frozen {label} drift: {observed!r} != {expected!r}"
        )


def _verify_response_blind(recomputed, receipt, contract) -> None:
    result = receipt["result"]
    _assert_equal("response-blind status", result["status"], "RESPONSE_BLIND_GEOMETRY_HEADER_PASS")
    _assert_equal("archive sha256", recomputed["archive"]["sha256"], contract["source"]["archive_sha256"])
    _assert_equal("receipt archive sha256", result["archive_sha256"], contract["source"]["archive_sha256"])
    frozen = contract["frozen_partition"]
    _assert_equal("deployment count", recomputed["geometry"]["deployment_count"], frozen["deployment_count"])
    _assert_equal("training count", recomputed["geometry"]["training_deployment_count"], frozen["training_count"])
    _assert_equal("heldout count", recomputed["geometry"]["heldout_deployment_count"], frozen["heldout_count"])
    _assert_equal("max training longitude", recomputed["geometry"]["max_training_longitude"], frozen["max_training_longitude"])
    _assert_equal("min heldout longitude", recomputed["geometry"]["min_heldout_longitude"], frozen["min_heldout_longitude"])
    _assert_equal("training ids hash", recomputed["fingerprints"]["training_ids_sha256"], frozen["training_ids_sha256"])
    _assert_equal("heldout ids hash", recomputed["fingerprints"]["heldout_ids_sha256"], frozen["heldout_ids_sha256"])
    _assert_equal("training role map hash", recomputed["fingerprints"]["training_role_map_sha256"], frozen["training_role_map_sha256"])
    _assert_equal("manifest hash", recomputed["fingerprints"]["manifest_sha256"], frozen["manifest_sha256"])


def _verify_temporal(
    archive_path: Path,
    response_blind_receipt,
    frozen_temporal,
    contract,
):
    observed = audit_e2_mica_temporal_integrity(
        archive_path,
        response_blind_receipt,
    )
    if observed["status"] != "TEMPORAL_INTEGRITY_PASS":
        raise ValueError(
            f"E2 MICA temporal integrity no longer passes: {observed['status']}"
        )
    quarantine = contract["temporal_quarantine"]
    _assert_equal(
        "temporal quarantine sha256",
        observed["quarantine"]["event_identity_set_sha256"],
        quarantine["event_identity_set_sha256"],
    )
    _assert_equal(
        "temporal quarantine count",
        observed["quarantine"]["event_count"],
        quarantine["quarantine_event_count"],
    )
    _assert_equal(
        "frozen temporal receipt quarantine sha256",
        frozen_temporal["quarantine"]["event_identity_set_sha256"],
        quarantine["event_identity_set_sha256"],
    )
    observed_ids = tuple(
        (row["deploymentID"], row["eventID"])
        for row in observed["quarantine"]["event_identities"]
    )
    frozen_ids = tuple(
        (row["deploymentID"], row["eventID"])
        for row in frozen_temporal["quarantine"]["event_identities"]
    )
    _assert_equal("temporal quarantine identities", observed_ids, frozen_ids)
    return observed, frozenset(observed_ids)


def _verify_climate(climate_payload, contract, expected_ids):
    if climate_payload.get("status") != "CLIMATE_QUALIFIED":
        raise ValueError("E2 MICA climate payload is not CLIMATE_QUALIFIED")
    frozen = contract["climate"]
    _assert_equal(
        "climate deployment sha256",
        climate_payload.get("deployment_climate_sha256"),
        frozen["deployment_climate_sha256"],
    )
    rows = tuple(climate_payload.get("deployment_climate", ()))
    if len(rows) != len(expected_ids):
        raise ValueError(
            f"E2 MICA climate row count drift: {len(rows)} != {len(expected_ids)}"
        )
    if _climate_rows_sha256(list(rows)) != frozen["deployment_climate_sha256"]:
        raise ValueError("E2 MICA climate row content hash drift")
    by_id = {}
    for row in rows:
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id or deployment_id in by_id:
            raise ValueError("E2 MICA climate deployment IDs must be unique")
        by_id[deployment_id] = dict(row)
    _assert_equal("climate deployment ID set", set(by_id), set(expected_ids))
    return by_id


def _read_deployments(
    archive: zipfile.ZipFile,
    entry: str,
    role_by_space: Mapping[str, str],
    climate_by_id: Mapping[str, Mapping[str, object]],
):
    payload = archive.read(entry).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(payload))
    required = {
        "deploymentID",
        "latitude",
        "longitude",
        "deploymentStart",
        "deploymentEnd",
    }
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError("E2 MICA deployments CSV lacks required columns")

    output = {}
    for index, row in enumerate(reader):
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id or deployment_id in output:
            raise ValueError("E2 MICA deploymentID values must be unique non-empty")
        if deployment_id not in role_by_space or deployment_id not in climate_by_id:
            raise ValueError(
                f"E2 MICA deployment {deployment_id!r} is outside frozen partition/climate"
            )
        try:
            latitude = float(str(row.get("latitude", "")).strip())
            longitude = float(str(row.get("longitude", "")).strip())
        except ValueError as exc:
            raise ValueError(
                f"E2 MICA deployment row {index} has non-numeric coordinates"
            ) from exc
        start = _parse_iso(row.get("deploymentStart", ""))
        end = _parse_iso(row.get("deploymentEnd", ""))
        effort = _active_effort_by_context(start, end)
        if not effort:
            raise ValueError(
                f"E2 MICA deployment {deployment_id!r} has no positive scored effort"
            )
        climate = climate_by_id[deployment_id]
        if abs(float(climate["latitude"]) - latitude) > 1e-10:
            raise ValueError("E2 MICA climate latitude drift")
        if abs(float(climate["longitude"]) - longitude) > 1e-10:
            raise ValueError("E2 MICA climate longitude drift")
        output[deployment_id] = {
            "latitude": latitude,
            "longitude": longitude,
            "start": start,
            "end": end,
            "effort": effort,
            "role": role_by_space[deployment_id],
            "precip_z_train": float(climate["precip_z_train"]),
        }
    return output


def _parse_positive_integer_count(value: str):
    text = str(value).strip()
    if not text:
        return None
    try:
        numeric = float(text)
    except ValueError as exc:
        raise ValueError(f"E2 MICA focal count is non-numeric: {text!r}") from exc
    if not math.isfinite(numeric):
        raise ValueError("E2 MICA focal count must be finite")
    if numeric <= 0.0:
        return None
    if not numeric.is_integer():
        raise ValueError(
            f"E2 MICA focal count must be an integer when positive: {text!r}"
        )
    return int(numeric)


def _read_focal_events(
    archive: zipfile.ZipFile,
    entry: str,
    deployments,
    quarantine,
    grid_keys,
):
    payload = archive.read(entry).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(payload))
    if reader.fieldnames is None or not REQUIRED_OBSERVATION_COLUMNS.issubset(
        set(reader.fieldnames)
    ):
        raise ValueError("E2 MICA observations CSV lacks required full-response columns")

    focal = {}
    rows_scanned = 0
    quarantined_rows_skipped = 0
    for index, row in enumerate(reader, start=2):
        rows_scanned += 1
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue

        # The quarantine firewall is deliberately applied before scientificName/count.
        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        if not deployment_id or not event_id:
            raise ValueError(
                f"E2 MICA animal event row {index} lacks deployment/event identity"
            )
        identity = (deployment_id, event_id)
        if identity in quarantine:
            quarantined_rows_skipped += 1
            continue

        if str(row.get("scientificName", "")).strip() != FOCAL_SCIENTIFIC_NAME:
            continue
        if deployment_id not in deployments:
            raise ValueError("E2 MICA focal event references unknown deployment")

        event_start = _parse_iso(row.get("eventStart", ""))
        meta = deployments[deployment_id]
        if not (meta["start"] <= event_start <= meta["end"]):
            raise ValueError(
                f"E2 MICA non-quarantined focal event {event_id!r} lies outside deployment"
            )

        record = focal.setdefault(
            identity,
            {
                "deployment_id": deployment_id,
                "event_id": event_id,
                "event_start": event_start,
                "positive_counts": set(),
            },
        )
        if record["event_start"] != event_start:
            raise ValueError("E2 MICA focal event has inconsistent eventStart")
        count = _parse_positive_integer_count(row.get("count", ""))
        if count is not None:
            record["positive_counts"].add(count)

    for identity, record in focal.items():
        if len(record["positive_counts"]) > 1:
            raise ValueError(
                f"E2 MICA focal event {identity!r} has conflicting positive counts: "
                f"{sorted(record['positive_counts'])!r}"
            )
    return focal, rows_scanned, quarantined_rows_skipped


def _sparse_increment(block, key, amount=1):
    block[key] = int(block.get(key, 0)) + int(amount)


def build_e2_mica_empirical_fixture(
    *,
    archive_path: str | Path,
    climate_payload: Mapping[str, object],
    response_blind_receipt: Mapping[str, object],
    temporal_receipt: Mapping[str, object],
    full_contract: Mapping[str, object],
) -> E2MicaEmpiricalFixture:
    """Open the frozen MICA response once and build the unchanged R5b graph."""

    path = Path(archive_path)
    source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    _assert_equal(
        "source archive sha256",
        source_sha256,
        full_contract["source"]["archive_sha256"],
    )

    recomputed = qualify_e2_mica_archive(path)
    _verify_response_blind(recomputed, response_blind_receipt, full_contract)
    temporal_observed, quarantine = _verify_temporal(
        path,
        response_blind_receipt,
        temporal_receipt,
        full_contract,
    )

    manifest = recomputed["manifest"]
    train_spaces = tuple(manifest["training_deployment_ids"])
    heldout_spaces = tuple(manifest["heldout_deployment_ids"])
    training_roles = dict(manifest["training_role_by_deployment"])
    role_by_space = {
        **training_roles,
        **{space: "heldout_state_annotated" for space in heldout_spaces},
    }
    all_spaces = tuple(sorted(role_by_space))
    climate_by_id = _verify_climate(
        climate_payload,
        full_contract,
        all_spaces,
    )

    with zipfile.ZipFile(path) as archive:
        names = {PurePosixPath(name).name for name in archive.namelist()}
        missing = REQUIRED_MEMBERS - names
        if missing:
            raise ValueError(f"E2 MICA archive missing members: {sorted(missing)}")
        deployments_entry = _find_unique_entry(archive, "deployments.csv")
        observations_entry = _find_unique_entry(archive, "observations.csv")
        deployments = _read_deployments(
            archive,
            deployments_entry,
            role_by_space,
            climate_by_id,
        )

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
            raise ValueError("E2 MICA training latitude/eastness lacks variation")

        doy_values = tuple(sorted({
            doy
            for meta in deployments.values()
            for doy, _hour in meta["effort"]
        }))
        hour_values = tuple(bin_[2] for bin_ in HOUR_BINS)
        grid = Grid(
            space=all_spaces,
            doy=doy_values,
            hour=hour_values,
        )
        grid_key_set = set(grid.keys)

        focal_events, response_rows_scanned, quarantined_rows_skipped = _read_focal_events(
            archive,
            observations_entry,
            deployments,
            quarantine,
            grid_key_set,
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
        if role_by_space[space] == "opportunistic_presence"
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    )
    calibrated_effort = {
        (space, doy, hour): effort
        for space in train_spaces
        if role_by_space[space] == "calibrated_presence"
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    }
    annotated_spaces = tuple(
        space
        for space in all_spaces
        if role_by_space[space] in {
            "state_annotated",
            "heldout_state_annotated",
        }
    )
    annotated_effort = {
        (space, doy, hour): effort
        for space in annotated_spaces
        for (doy, hour), effort in deployments[space]["effort"].items()
        if effort > 0.0
    }

    presence_counts = {
        "opportunistic_presence": {},
        "calibrated_presence": {},
    }
    state_counts = {
        "state_annotated": {"solitary": {}, "group": {}},
        "state_calibration": {"solitary": {}, "group": {}},
    }
    focal_events_by_role = {
        "opportunistic_presence": 0,
        "calibrated_presence": 0,
        "state_annotated": 0,
        "state_calibration": 0,
        "heldout_state_annotated": 0,
    }
    unlabeled_by_role = {name: 0 for name in focal_events_by_role}

    for event in focal_events.values():
        deployment_id = event["deployment_id"]
        meta = deployments[deployment_id]
        role = role_by_space[deployment_id]
        focal_events_by_role[role] += 1
        start = event["event_start"]
        context = (
            deployment_id,
            _representative_doy(start),
            _hour_bin(start.hour),
        )
        if context not in grid_key_set:
            raise ValueError("E2 MICA focal event maps outside frozen model grid")

        if role == "opportunistic_presence":
            _sparse_increment(
                presence_counts["opportunistic_presence"],
                context,
            )
        elif role == "calibrated_presence":
            _sparse_increment(
                presence_counts["calibrated_presence"],
                context,
            )

        positives = tuple(sorted(event["positive_counts"]))
        if not positives:
            unlabeled_by_role[role] += 1
            continue
        count = positives[0]
        state = "solitary" if count == 1 else "group"
        if role in {"state_annotated", "heldout_state_annotated"}:
            _sparse_increment(
                state_counts["state_annotated"][state],
                context,
            )
        elif role == "state_calibration":
            _sparse_increment(
                state_counts["state_calibration"][state],
                context,
            )

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

    data = {
        "presence_opportunistic": {
            "sp": dict(presence_counts["opportunistic_presence"])
        },
        "presence_calibrated": {
            "sp": dict(presence_counts["calibrated_presence"])
        },
        "annotated": {
            "sp": {
                state: dict(state_counts["state_annotated"][state])
                for state in STATES.states
            }
        },
        "state_calibration": {
            "sp": {
                state: dict(state_counts["state_calibration"][state])
                for state in STATES.states
            }
        },
    }

    def _state_total(role_name, state, spaces):
        space_set = set(spaces)
        return sum(
            int(count)
            for key, count in state_counts[role_name][state].items()
            if key[0] in space_set
        )

    train_annotated_spaces = tuple(
        space
        for space in train_spaces
        if role_by_space[space] == "state_annotated"
    )
    calibration_spaces = tuple(
        space
        for space in train_spaces
        if role_by_space[space] == "state_calibration"
    )
    state_diagnostics = {
        "training_state_annotated": {
            state: _state_total(
                "state_annotated", state, train_annotated_spaces
            )
            for state in STATES.states
        },
        "state_calibration": {
            state: _state_total(
                "state_calibration", state, calibration_spaces
            )
            for state in STATES.states
        },
        "heldout_state_annotated": {
            state: _state_total(
                "state_annotated", state, heldout_spaces
            )
            for state in STATES.states
        },
    }

    stops = full_contract["consumed_estimability_stops"]
    if focal_events_by_role["opportunistic_presence"] < int(
        stops["minimum_opportunistic_focal_events"]
    ):
        raise ValueError("E2 MICA opportunistic focal events below frozen minimum")
    if focal_events_by_role["calibrated_presence"] < int(
        stops["minimum_calibrated_focal_events"]
    ):
        raise ValueError("E2 MICA calibrated focal events below frozen minimum")
    for state in STATES.states:
        if state_diagnostics["training_state_annotated"][state] < int(
            stops["minimum_training_state_annotated_each_state"]
        ):
            raise ValueError(
                f"E2 MICA training annotated {state} below frozen minimum"
            )
        if state_diagnostics["state_calibration"][state] < int(
            stops["minimum_state_calibration_each_state"]
        ):
            raise ValueError(
                f"E2 MICA state calibration {state} below frozen minimum"
            )
        if state_diagnostics["heldout_state_annotated"][state] < int(
            stops["minimum_heldout_state_annotated_each_state"]
        ):
            raise ValueError(
                f"E2 MICA heldout annotated {state} below frozen minimum"
            )

    heldout_effort_spaces = {
        key[0] for key, value in annotated_effort.items()
        if value > 0.0 and key[0] in set(heldout_spaces)
    }
    if heldout_effort_spaces != set(heldout_spaces):
        missing = sorted(set(heldout_spaces) - heldout_effort_spaces)
        raise ValueError(
            f"E2 MICA heldout deployment(s) lack scored effort: {missing[:3]!r}"
        )

    diagnostics = {
        "deployment_count": len(all_spaces),
        "training_deployment_count": len(train_spaces),
        "heldout_deployment_count": len(heldout_spaces),
        "doy_count": len(doy_values),
        "hour_count": len(hour_values),
        "grid_context_count": len(grid.keys),
        "response_rows_scanned": response_rows_scanned,
        "quarantine_event_count": len(quarantine),
        "quarantined_rows_skipped_before_focal_filter": quarantined_rows_skipped,
        "temporal_recomputed_quarantine_sha256": temporal_observed["quarantine"][
            "event_identity_set_sha256"
        ],
        "focal_event_count": len(focal_events),
        "focal_events_by_role": dict(focal_events_by_role),
        "unlabeled_focal_events_by_role": dict(unlabeled_by_role),
        "state_counts": state_diagnostics,
        "source_sha256": source_sha256,
        "climate_sha256": climate_payload["deployment_climate_sha256"],
    }
    diagnostics["fixture_fingerprint_sha256"] = _canonical_sha256(diagnostics)

    return E2MicaEmpiricalFixture(
        model=model,
        covariates=covariates,
        data=data,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        stream_by_space=role_by_space,
        source_sha256=source_sha256,
        climate_sha256=climate_payload["deployment_climate_sha256"],
        diagnostics=diagnostics,
    )
