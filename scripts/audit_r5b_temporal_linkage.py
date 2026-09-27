#!/usr/bin/env python3
"""Descriptive temporal-linkage audit for the consumed R5b empirical response."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "replication" / "R5B_TEMPORAL_LINKAGE_AUDIT_CONTRACT.json"
OUTPUT = ROOT / "artifacts" / "r5b_temporal_linkage_audit.json"


def _parse_iso(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        raise ValueError("empty timestamp")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone offset: {text!r}")
    return parsed


def _offset_text(value: datetime) -> str:
    offset = value.utcoffset()
    if offset is None:
        return "naive"
    seconds = int(offset.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "esdm-r5b-temporal-linkage-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
        return response.read()


def _read_csv(payload: bytes):
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    return tuple(reader.fieldnames or ()), list(reader)


def _quantile(values, probability: float):
    rows = sorted(float(value) for value in values)
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]
    p = float(probability)
    position = p * (len(rows) - 1)
    lo = int(math.floor(position))
    hi = int(math.ceil(position))
    if lo == hi:
        return rows[lo]
    w = position - lo
    return rows[lo] * (1.0 - w) + rows[hi] * w


def _summary(values):
    rows = tuple(float(value) for value in values)
    if not rows:
        return {
            "n": 0,
            "min": None,
            "q25": None,
            "median": None,
            "q75": None,
            "max": None,
            "mean": None
        }
    return {
        "n": len(rows),
        "min": min(rows),
        "q25": _quantile(rows, 0.25),
        "median": _quantile(rows, 0.50),
        "q75": _quantile(rows, 0.75),
        "max": max(rows),
        "mean": math.fsum(rows) / len(rows)
    }


def _evaluate_event(event, deployments):
    deployment_id = event["deployment_id"]
    if deployment_id not in deployments:
        return {
            **event,
            "status": "missing_deployment",
            "signed_offset_seconds": None,
            "absolute_offset_seconds": None,
            "deployment_start": None,
            "deployment_end": None,
            "event_timezone_offset": _offset_text(event["event_start"]),
            "deployment_start_timezone_offset": None,
            "deployment_end_timezone_offset": None,
        }

    dep = deployments[deployment_id]
    event_start = event["event_start"]
    start = dep["start"]
    end = dep["end"]
    if event_start < start:
        signed = (event_start - start).total_seconds()
        status = "before_start"
    elif event_start > end:
        signed = (event_start - end).total_seconds()
        status = "after_end"
    else:
        signed = 0.0
        status = "inside"

    return {
        **event,
        "status": status,
        "signed_offset_seconds": signed,
        "absolute_offset_seconds": abs(signed),
        "deployment_start": start.isoformat(),
        "deployment_end": end.isoformat(),
        "event_timezone_offset": _offset_text(event_start),
        "deployment_start_timezone_offset": _offset_text(start),
        "deployment_end_timezone_offset": _offset_text(end),
    }


def _event_map(rows, *, focal_only: bool):
    events = {}
    for index, row in enumerate(rows):
        if str(row.get("observationLevel", "")).strip() != "event":
            continue
        if str(row.get("observationType", "")).strip() != "animal":
            continue
        if focal_only and str(row.get("scientificName", "")).strip() != "Cervus nippon":
            continue

        deployment_id = str(row.get("deploymentID", "")).strip()
        event_id = str(row.get("eventID", "")).strip()
        if not deployment_id or not event_id:
            continue

        try:
            event_start = _parse_iso(row.get("eventStart", ""))
        except Exception:
            continue

        key = (deployment_id, event_id)
        current = events.get(key)
        if current is None:
            events[key] = {
                "deployment_id": deployment_id,
                "event_id": event_id,
                "event_start": event_start,
                "observation_rows": 1,
                "scientific_names": {
                    str(row.get("scientificName", "")).strip()
                },
            }
            continue

        if current["event_start"] != event_start:
            current.setdefault("inconsistent_event_starts", set()).add(
                event_start.isoformat()
            )
        current["observation_rows"] += 1
        current["scientific_names"].add(
            str(row.get("scientificName", "")).strip()
        )

    output = []
    for value in events.values():
        output.append({
            "deployment_id": value["deployment_id"],
            "event_id": value["event_id"],
            "event_start": value["event_start"],
            "event_start_iso": value["event_start"].isoformat(),
            "observation_rows": int(value["observation_rows"]),
            "scientific_names": sorted(value["scientific_names"]),
            "inconsistent_event_starts": sorted(
                value.get("inconsistent_event_starts", ())
            ),
        })
    return tuple(output)


def _audit_group(events, deployments):
    evaluated = tuple(_evaluate_event(event, deployments) for event in events)
    violations = tuple(
        row for row in evaluated
        if row["status"] in {"before_start", "after_end", "missing_deployment"}
    )
    interval_violations = tuple(
        row for row in violations
        if row["status"] in {"before_start", "after_end"}
    )
    counts = Counter(row["status"] for row in evaluated)
    by_deployment = Counter(
        row["deployment_id"] for row in interval_violations
    )
    timezone_pairs = Counter(
        (
            row["event_timezone_offset"],
            row["deployment_start_timezone_offset"],
            row["deployment_end_timezone_offset"],
        )
        for row in interval_violations
    )
    absolute_offsets = [
        row["absolute_offset_seconds"] for row in interval_violations
    ]
    return {
        "event_count": len(evaluated),
        "inside_count": counts.get("inside", 0),
        "before_start_count": counts.get("before_start", 0),
        "after_end_count": counts.get("after_end", 0),
        "missing_deployment_count": counts.get("missing_deployment", 0),
        "interval_violation_count": len(interval_violations),
        "interval_violation_rate": (
            len(interval_violations) / len(evaluated)
            if evaluated else None
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
        "violation_counts_by_deployment": [
            {"deployment_id": key, "count": count}
            for key, count in sorted(
                by_deployment.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "timezone_offset_triplets": [
            {
                "event": key[0],
                "deployment_start": key[1],
                "deployment_end": key[2],
                "count": count,
            }
            for key, count in sorted(
                timezone_pairs.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
        "violations": [
            {
                key: (
                    value.isoformat()
                    if isinstance(value, datetime)
                    else value
                )
                for key, value in row.items()
            }
            for row in interval_violations
        ],
    }


def main() -> int:
    cfg = json.loads(CONTRACT.read_text(encoding="utf-8"))
    payload = _get(cfg["source"]["url"])
    md5 = hashlib.md5(payload).hexdigest()  # noqa: S324 provenance only
    sha256 = hashlib.sha256(payload).hexdigest()
    if md5 != cfg["source"]["expected_md5"]:
        raise RuntimeError(f"source MD5 drift: {md5}")
    if sha256 != cfg["source"]["expected_sha256"]:
        raise RuntimeError(f"source SHA256 drift: {sha256}")

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        missing = set(cfg["source"]["required_members"]) - set(archive.namelist())
        if missing:
            raise RuntimeError(f"archive missing required members: {sorted(missing)}")
        deployment_columns, deployment_rows = _read_csv(
            archive.read("deployments.csv")
        )
        observation_columns, observation_rows = _read_csv(
            archive.read("observations.csv")
        )

    required_deployment = {
        "deploymentID", "deploymentStart", "deploymentEnd"
    }
    if not required_deployment.issubset(set(deployment_columns)):
        raise RuntimeError("deployment schema lacks temporal audit columns")
    required_observation = {
        "deploymentID", "eventID", "eventStart",
        "observationLevel", "observationType", "scientificName"
    }
    if not required_observation.issubset(set(observation_columns)):
        raise RuntimeError("observation schema lacks temporal audit columns")

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
        prior = deployments.get(deployment_id)
        value = {"start": start, "end": end}
        if prior is not None and prior != value:
            raise RuntimeError(
                f"deployment {deployment_id!r} has inconsistent intervals"
            )
        deployments[deployment_id] = value

    all_animal_events = _event_map(observation_rows, focal_only=False)
    focal_events = _event_map(observation_rows, focal_only=True)
    all_audit = _audit_group(all_animal_events, deployments)
    focal_audit = _audit_group(focal_events, deployments)

    focal_violation_ids = {
        row["event_id"] for row in focal_audit["violations"]
    }
    result = {
        "schema": "esdm.replication.r5b_temporal_linkage_audit.v1",
        "status": "AUDIT_COMPLETE",
        "programme_class": cfg["programme_class"],
        "source": {
            "file_name": cfg["source"]["file_name"],
            "bytes": len(payload),
            "md5": md5,
            "sha256": sha256,
        },
        "deployment_count": len(deployments),
        "observation_row_count": len(observation_rows),
        "all_animal_events": all_audit,
        "focal_cervus_nippon_events": focal_audit,
        "terminal_event_7815128_is_violation": "7815128" in focal_violation_ids,
        "model_fits": 0,
        "heldout_scores": 0,
        "first_empirical_result_modified": False,
        "repair_performed": False,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "status": result["status"],
        "deployment_count": result["deployment_count"],
        "observation_row_count": result["observation_row_count"],
        "all_animal_interval_violation_count": all_audit["interval_violation_count"],
        "focal_interval_violation_count": focal_audit["interval_violation_count"],
        "terminal_event_7815128_is_violation": result["terminal_event_7815128_is_violation"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
