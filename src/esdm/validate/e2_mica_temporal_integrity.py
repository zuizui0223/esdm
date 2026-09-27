"""Response-limited temporal-integrity audit for frozen E2 MICA candidate."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Mapping
import zipfile

from .e2_mica_response_blind import qualify_e2_mica_archive


ALLOWED_COLUMNS = (
    "deploymentID",
    "eventID",
    "eventStart",
    "observationLevel",
    "observationType",
)


@dataclass(frozen=True, slots=True)
class EventRecord:
    deployment_id: str
    event_id: str
    event_start: datetime


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_datetime(value: str, *, name: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is empty")
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{name} is not ISO-8601 parseable") from exc


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


def _read_deployment_intervals(
    archive: zipfile.ZipFile,
    entry: str,
) -> dict[str, tuple[datetime, datetime]]:
    payload = archive.read(entry).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(payload))
    if reader.fieldnames is None:
        raise ValueError("deployments CSV has no header")
    required = {"deploymentID", "deploymentStart", "deploymentEnd"}
    if not required.issubset(set(reader.fieldnames)):
        raise ValueError("deployments CSV lacks temporal-integrity columns")

    output: dict[str, tuple[datetime, datetime]] = {}
    for index, row in enumerate(reader):
        deployment_id = str(row.get("deploymentID", "")).strip()
        if not deployment_id:
            raise ValueError(f"deployments[{index}] has empty deploymentID")
        start = _parse_datetime(
            row.get("deploymentStart", ""),
            name=f"deployments[{index}].deploymentStart",
        )
        end = _parse_datetime(
            row.get("deploymentEnd", ""),
            name=f"deployments[{index}].deploymentEnd",
        )
        if end < start:
            raise ValueError(f"deployment {deployment_id!r} ends before it starts")
        value = (start, end)
        prior = output.get(deployment_id)
        if prior is not None and prior != value:
            raise ValueError(
                f"deployment {deployment_id!r} has inconsistent temporal intervals"
            )
        output[deployment_id] = value
    return output


def _project_temporal_rows(
    archive: zipfile.ZipFile,
    entry: str,
) -> tuple[
    int,
    dict[tuple[str, str], EventRecord],
    dict[str, int],
]:
    with archive.open(entry, "r") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("observations CSV is empty") from exc

        columns = [str(value).strip() for value in header]
        index = {name: position for position, name in enumerate(columns)}
        missing = [name for name in ALLOWED_COLUMNS if name not in index]
        if missing:
            raise ValueError(f"observations CSV missing temporal columns: {missing!r}")

        events: dict[tuple[str, str], EventRecord] = {}
        counters = {
            "observation_rows_scanned": 0,
            "animal_event_rows": 0,
            "missing_event_identity_rows": 0,
            "unparseable_event_time_rows": 0,
            "inconsistent_event_start_identities": 0,
        }
        inconsistent_ids: set[tuple[str, str]] = set()

        for row_index, row in enumerate(reader, start=2):
            counters["observation_rows_scanned"] += 1
            if len(row) < len(columns):
                raise ValueError(
                    f"observations row {row_index} has fewer fields than header"
                )

            observation_level = row[index["observationLevel"]].strip()
            observation_type = row[index["observationType"]].strip()
            if observation_level != "event" or observation_type != "animal":
                continue
            counters["animal_event_rows"] += 1

            deployment_id = row[index["deploymentID"]].strip()
            event_id = row[index["eventID"]].strip()
            if not deployment_id or not event_id:
                counters["missing_event_identity_rows"] += 1
                continue

            try:
                event_start = _parse_datetime(
                    row[index["eventStart"]],
                    name=f"observations[{row_index}].eventStart",
                )
            except ValueError:
                counters["unparseable_event_time_rows"] += 1
                continue

            key = (deployment_id, event_id)
            current = events.get(key)
            if current is None:
                events[key] = EventRecord(
                    deployment_id=deployment_id,
                    event_id=event_id,
                    event_start=event_start,
                )
                continue
            if current.event_start != event_start:
                inconsistent_ids.add(key)

        counters["inconsistent_event_start_identities"] = len(inconsistent_ids)
        return counters["observation_rows_scanned"], events, counters


def _compare_response_blind(
    observed: Mapping[str, object],
    frozen: Mapping[str, object],
) -> None:
    result = frozen["result"]
    if observed["status"] != "RESPONSE_BLIND_GEOMETRY_HEADER_PASS":
        raise ValueError("recomputed response-blind qualification did not pass")
    if observed["candidate_id"] != "MICA_MUSKRAT":
        raise ValueError("recomputed response-blind candidate drifted")

    archive = observed["archive"]
    geometry = observed["geometry"]
    roles = observed["roles"]
    fingerprints = observed["fingerprints"]

    expected_scalars = {
        "archive_sha256": (archive["sha256"], result["archive_sha256"]),
        "deployments_sha256": (
            archive["deployments_sha256"],
            result["deployments_sha256"],
        ),
        "deployment_count": (
            geometry["deployment_count"],
            result["deployment_count"],
        ),
        "training_deployment_count": (
            geometry["training_deployment_count"],
            result["training_deployment_count"],
        ),
        "heldout_deployment_count": (
            geometry["heldout_deployment_count"],
            result["heldout_deployment_count"],
        ),
        "max_training_longitude": (
            geometry["max_training_longitude"],
            result["max_training_longitude"],
        ),
        "min_heldout_longitude": (
            geometry["min_heldout_longitude"],
            result["min_heldout_longitude"],
        ),
        "longitude_gap": (
            geometry["longitude_gap"],
            result["longitude_gap"],
        ),
        "training_role_counts": (
            roles["training_counts"],
            result["training_role_counts"],
        ),
    }
    for name, (left, right) in expected_scalars.items():
        if left != right:
            raise ValueError(f"response-blind {name} mismatch")

    for name, expected in result["fingerprints"].items():
        if fingerprints.get(name) != expected:
            raise ValueError(f"response-blind fingerprint mismatch: {name}")


def audit_e2_mica_temporal_integrity(
    archive_path: str | Path,
    response_blind_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Audit temporal linkage without using focal-taxon or count response values."""

    path = Path(archive_path)
    recomputed = qualify_e2_mica_archive(path)
    _compare_response_blind(recomputed, response_blind_receipt)

    with zipfile.ZipFile(path) as archive:
        deployments_entry = _find_unique_entry(archive, "deployments.csv")
        observations_entry = _find_unique_entry(archive, "observations.csv")
        deployments = _read_deployment_intervals(archive, deployments_entry)
        row_count, events, counters = _project_temporal_rows(
            archive,
            observations_entry,
        )

    before_start = 0
    after_end = 0
    after_end_over_24h = 0
    missing_deployment = 0
    quarantine: list[tuple[str, str]] = []
    maximum_after_end_seconds = 0.0

    for key in sorted(events):
        event = events[key]
        interval = deployments.get(event.deployment_id)
        if interval is None:
            missing_deployment += 1
            continue
        start, end = interval
        try:
            if event.event_start < start:
                before_start += 1
            elif event.event_start > end:
                after_end += 1
                seconds = (event.event_start - end).total_seconds()
                maximum_after_end_seconds = max(maximum_after_end_seconds, seconds)
                if seconds > 86400:
                    after_end_over_24h += 1
                else:
                    quarantine.append(key)
        except TypeError as exc:
            raise ValueError(
                "event and deployment timestamps mix timezone-aware and naive values"
            ) from exc

    unique_event_count = len(events)
    quarantine = sorted(set(quarantine))
    quarantine_fraction = (
        len(quarantine) / unique_event_count if unique_event_count else None
    )
    quarantine_payload = [
        {"deploymentID": deployment_id, "eventID": event_id}
        for deployment_id, event_id in quarantine
    ]
    quarantine_sha256 = _canonical_sha256(quarantine_payload)

    stop_reasons: list[str] = []
    if counters["missing_event_identity_rows"]:
        stop_reasons.append("missing_event_identity")
    if counters["unparseable_event_time_rows"]:
        stop_reasons.append("unparseable_event_time")
    if counters["inconsistent_event_start_identities"]:
        stop_reasons.append("inconsistent_event_start")
    if missing_deployment:
        stop_reasons.append("missing_deployment")
    if before_start:
        stop_reasons.append("before_deployment_start")
    if after_end_over_24h:
        stop_reasons.append("after_end_over_24_hours")
    if quarantine_fraction is None:
        stop_reasons.append("no_unique_animal_events")
    elif quarantine_fraction > 0.005:
        stop_reasons.append("quarantine_fraction_above_0_005")

    passed = not stop_reasons
    return {
        "schema_version": 1,
        "result_id": "e2-mica-temporal-integrity-v1",
        "status": (
            "TEMPORAL_INTEGRITY_PASS"
            if passed
            else "STOP_TEMPORAL_INTEGRITY"
        ),
        "candidate_id": "MICA_MUSKRAT",
        "source_reverification": {
            "response_blind_recomputed": True,
            "archive_sha256": recomputed["archive"]["sha256"],
            "deployments_sha256": recomputed["archive"]["deployments_sha256"],
            "fingerprints": recomputed["fingerprints"],
        },
        "scan": {
            "observations_data_rows_scanned": row_count,
            "allowed_columns_used": list(ALLOWED_COLUMNS),
            "scientific_name_values_read": False,
            "count_values_read": False,
            "focal_taxon_filtering_performed": False,
            "state_mapping_performed": False,
            **counters,
        },
        "events": {
            "unique_animal_event_count": unique_event_count,
            "inside_count": (
                unique_event_count
                - before_start
                - after_end
                - missing_deployment
            ),
            "before_start_count": before_start,
            "after_end_count": after_end,
            "after_end_over_24h_count": after_end_over_24h,
            "missing_deployment_count": missing_deployment,
            "maximum_after_end_seconds": maximum_after_end_seconds,
        },
        "quarantine": {
            "event_count": len(quarantine),
            "fraction_of_unique_animal_events": quarantine_fraction,
            "maximum_allowed_fraction": 0.005,
            "maximum_lateness_seconds": 86400,
            "event_identities": quarantine_payload,
            "event_identity_set_sha256": quarantine_sha256,
        },
        "decision": {
            "passed": passed,
            "stop_reasons": stop_reasons,
            "authorizes_full_response": False,
            "requires_separate_full_response_authorization": True,
        },
        "response_boundary": {
            "scientific_name_values_read": False,
            "count_values_read": False,
            "taxon_frequencies_computed": False,
            "focal_event_counts_computed": False,
            "state_frequencies_computed": False,
            "model_fits": 0,
            "heldout_scores": 0,
            "full_response_opened": False,
        },
    }
