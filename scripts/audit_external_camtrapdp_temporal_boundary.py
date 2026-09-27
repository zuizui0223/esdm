#!/usr/bin/env python3
"""Independent Camtrap DP temporal-boundary replication on Amsterdam pilot2."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT / "docs" / "replication"
    / "CAMTRAPDP_EXTERNAL_TEMPORAL_AUDIT_CONTRACT.json"
)
OUTPUT = ROOT / "artifacts" / "camtrapdp_external_temporal_audit.json"


def _parse_iso(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        raise ValueError("empty timestamp")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone offset: {text!r}")
    return parsed


def _offset_text(value: datetime) -> str:
    delta = value.utcoffset()
    if delta is None:
        return "naive"
    seconds = int(delta.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _download_to_file(url: str, target: Path):
    md5 = hashlib.md5()  # noqa: S324 provenance only
    sha256 = hashlib.sha256()
    total = 0
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "esdm-camtrapdp-external-temporal-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
        with target.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                md5.update(chunk)
                sha256.update(chunk)
                total += len(chunk)
    return total, md5.hexdigest(), sha256.hexdigest()


def _unique_member(archive, basename: str) -> str:
    matches = [
        name for name in archive.namelist()
        if Path(name).name == basename
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {basename!r}, found {len(matches)}"
        )
    return matches[0]


def _read_csv(archive, member: str):
    payload = archive.read(member)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    return tuple(reader.fieldnames or ()), list(reader)


def _quantile(values, probability):
    rows = sorted(float(value) for value in values)
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    position = float(probability) * (len(rows) - 1)
    lo = int(math.floor(position))
    hi = int(math.ceil(position))
    if lo == hi:
        return rows[lo]
    weight = position - lo
    return rows[lo] * (1.0 - weight) + rows[hi] * weight


def _summary(values):
    rows = tuple(float(value) for value in values)
    if not rows:
        return {
            "n": 0, "min": None, "q25": None, "median": None,
            "q75": None, "max": None, "mean": None
        }
    return {
        "n": len(rows),
        "min": min(rows),
        "q25": _quantile(rows, 0.25),
        "median": _quantile(rows, 0.50),
        "q75": _quantile(rows, 0.75),
        "max": max(rows),
        "mean": math.fsum(rows) / len(rows),
    }


def main() -> int:
    cfg = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = cfg["source"]

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / source["file_name"]
        total, md5, sha256 = _download_to_file(
            source["url"], archive_path
        )
        if md5 != source["expected_md5"]:
            raise RuntimeError(f"source MD5 drift: {md5}")

        with zipfile.ZipFile(archive_path) as archive:
            deployment_member = _unique_member(archive, "deployments.csv")
            observation_member = _unique_member(archive, "observations.csv")
            deployment_columns, deployment_rows = _read_csv(
                archive, deployment_member
            )
            observation_columns, observation_rows = _read_csv(
                archive, observation_member
            )

    required_deployment = {
        "deploymentID", "deploymentStart", "deploymentEnd"
    }
    missing = required_deployment - set(deployment_columns)
    if missing:
        raise RuntimeError(
            f"deployments.csv missing temporal columns: {sorted(missing)}"
        )

    required_observation = {
        "deploymentID", "eventID", "eventStart",
        "observationLevel", "observationType"
    }
    missing = required_observation - set(observation_columns)
    if missing:
        raise RuntimeError(
            f"observations.csv missing temporal columns: {sorted(missing)}"
        )

    deployments = {}
    for row in deployment_rows:
        deployment_id = str(row["deploymentID"]).strip()
        if not deployment_id:
            continue
        start = _parse_iso(row["deploymentStart"])
        end = _parse_iso(row["deploymentEnd"])
        if end <= start:
            raise RuntimeError(
                f"deployment {deployment_id!r} has non-positive interval"
            )
        value = (start, end)
        prior = deployments.get(deployment_id)
        if prior is not None and prior != value:
            raise RuntimeError(
                f"deployment {deployment_id!r} has inconsistent intervals"
            )
        deployments[deployment_id] = value

    events = {}
    skipped_unparseable = 0
    for row in observation_rows:
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue
        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        if not deployment_id or not event_id:
            continue
        try:
            event_start = _parse_iso(row.get("eventStart", ""))
        except Exception:
            skipped_unparseable += 1
            continue

        key = (deployment_id, event_id)
        prior = events.get(key)
        if prior is not None and prior != event_start:
            raise RuntimeError(
                f"event {event_id!r} has inconsistent eventStart values"
            )
        events[key] = event_start

    counts = Counter()
    affected = Counter()
    timezone_triplets = Counter()
    absolute_offsets = []
    violation_details = []

    for (deployment_id, event_id), event_start in events.items():
        if deployment_id not in deployments:
            counts["missing_deployment"] += 1
            continue
        start, end = deployments[deployment_id]
        if event_start < start:
            status = "before_start"
            signed = (event_start - start).total_seconds()
        elif event_start > end:
            status = "after_end"
            signed = (event_start - end).total_seconds()
        else:
            counts["inside"] += 1
            continue

        counts[status] += 1
        affected[deployment_id] += 1
        absolute_offsets.append(abs(signed))
        timezone_triplets[(
            _offset_text(event_start),
            _offset_text(start),
            _offset_text(end),
        )] += 1
        violation_details.append({
            "deployment_id": deployment_id,
            "event_id": event_id,
            "event_start": event_start.isoformat(),
            "deployment_start": start.isoformat(),
            "deployment_end": end.isoformat(),
            "status": status,
            "signed_offset_seconds": signed,
            "absolute_offset_seconds": abs(signed),
        })

    interval_violations = (
        counts["before_start"] + counts["after_end"]
    )
    result = {
        "schema": "esdm.replication.camtrapdp_external_temporal_audit.v1",
        "status": "AUDIT_COMPLETE",
        "source": {
            "doi": source["doi"],
            "pilot": source["pilot"],
            "file_name": source["file_name"],
            "bytes": total,
            "md5": md5,
            "sha256": sha256,
            "deployment_member": deployment_member,
            "observation_member": observation_member,
        },
        "deployment_count": len(deployments),
        "observation_row_count": len(observation_rows),
        "unique_animal_event_count": len(events),
        "unparseable_animal_event_rows_skipped": skipped_unparseable,
        "inside_count": counts["inside"],
        "before_start_count": counts["before_start"],
        "after_end_count": counts["after_end"],
        "missing_deployment_count": counts["missing_deployment"],
        "interval_violation_count": interval_violations,
        "interval_violation_rate": (
            interval_violations / len(events) if events else None
        ),
        "absolute_offset_seconds": _summary(absolute_offsets),
        "violations_within_1_hour": sum(
            value <= 3600 for value in absolute_offsets
        ),
        "violations_within_24_hours": sum(
            value <= 86400 for value in absolute_offsets
        ),
        "violations_within_7_days": sum(
            value <= 7 * 86400 for value in absolute_offsets
        ),
        "affected_deployment_count": len(affected),
        "violation_counts_by_deployment": [
            {"deployment_id": key, "count": value}
            for key, value in sorted(
                affected.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "timezone_offset_triplets": [
            {
                "event": key[0],
                "deployment_start": key[1],
                "deployment_end": key[2],
                "count": value,
            }
            for key, value in sorted(
                timezone_triplets.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "violations": sorted(
            violation_details,
            key=lambda row: (
                row["deployment_id"],
                row["event_start"],
                row["event_id"],
            ),
        ),
        "model_fits": 0,
        "heldout_scores": 0,
        "interval_repair_performed": False,
        "first_empirical_endpoint_modified": False,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "status": result["status"],
        "deployment_count": result["deployment_count"],
        "unique_animal_event_count": result["unique_animal_event_count"],
        "interval_violation_count": result["interval_violation_count"],
        "interval_violation_rate": result["interval_violation_rate"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
