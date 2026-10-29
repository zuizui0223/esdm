#!/usr/bin/env python3
"""Known-reference-passage versus camera registration with auditable exposure.

Three distinct, joined, timestamp-validated source tables are REQUIRED.
Without time-stamped overlapping reference/camera intervals, independent
reference-passage rates cannot be verified. This is a reusable field-data
contract, NOT a new E5 qualified dataset or measured ecological result.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

SUPPORTED_WINDOWS = {"night", "midday"}
SAMPLING_SCHEMES = {"continuous_reference", "randomized_time_blocks"}
REQUIRED_EFFORT = {
    "site_id", "phase", "clock_bin", "camera_operational_minutes",
    "independent_reference_minutes", "reference_sampling_scheme",
}
REQUIRED_COVERAGE = {
    "interval_id", "site_id", "phase", "clock_bin", "reference_source_id",
    "camera_start", "camera_end", "reference_start", "reference_end",
}
REQUIRED_PASSAGES = {
    "independent_passage_id", "site_id", "phase", "clock_bin", "species",
    "reference_source_id", "reference_timestamp",
    "camera_triggered", "species_registered", "camera_event_id",
}


def _get_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not required.issubset(fields):
            raise ValueError(f"{path.name}: required headers missing: {sorted(required-fields)}")
        return list(reader)


def _positive(v: str, label: str) -> float:
    try:
        n = float(v)
    except (ValueError, TypeError):
        raise ValueError(f"{label}: not numeric") from None
    if not math.isfinite(n) or n <= 0:
        raise ValueError(f"{label}: must be finite and positive")
    return n


def _binary(v: str, label: str) -> int:
    if v not in ("0", "1"):
        raise ValueError(f"{label}: must be binary 0 or 1, not missing/unknown")
    return int(v)


def _stratum(row: dict[str, str]) -> tuple[str, str, str]:
    site = row["site_id"].strip()
    phase = row["phase"].strip()
    clock = row["clock_bin"].strip()
    if not site or not phase or clock not in SUPPORTED_WINDOWS:
        raise ValueError("site/phase/clock_bin missing or invalid")
    return site, phase, clock


def _aware(v: str, label: str) -> datetime:
    try:
        ts = datetime.fromisoformat(str(v).strip().replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError(f"{label}: invalid ISO datetime") from None
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError(f"{label}: explicit timezone offset required")
    return ts


def _clock(hour: int) -> str | None:
    return "night" if hour >= 21 or hour < 4 else (
        "midday" if 10 <= hour < 16 else None
    )


def _within_clock_window(start: datetime, end: datetime, clock: str) -> None:
    """Every part of a coverage interval must actually be in the stated bin."""
    if not start < end:
        raise ValueError("coverage interval start/end invalid")
    if start.utcoffset() != end.utcoffset():
        raise ValueError("coverage crossing timezone-offset transition must be split")
    max_minutes = 420 if clock == "night" else 360
    if (end - start).total_seconds() > max_minutes * 60 + 1e-6:
        raise ValueError("coverage interval longer than defined clock window")
    current = start
    while current < end:
        if _clock(current.hour) != clock:
            raise ValueError("coverage interval includes time outside declared clock bin")
        next_hour = current.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        current = min(next_hour, end)


def _read_effort(path: Path) -> dict[tuple[str, str, str], dict]:
    out = {}
    for row in _get_csv(path, REQUIRED_EFFORT):
        key = _stratum(row)
        if key in out:
            raise ValueError(f"duplicate effort stratum {key}")
        scheme = row["reference_sampling_scheme"].strip()
        if scheme not in SAMPLING_SCHEMES:
            raise ValueError("independent reference cannot be selected by camera trigger")
        camera = _positive(row["camera_operational_minutes"], "camera_operational_minutes")
        reference = _positive(row["independent_reference_minutes"], "independent_reference_minutes")
        if reference > camera:
            raise ValueError("reference overlap exceeds camera operational exposure")
        out[key] = {
            "camera_operational_minutes": camera,
            "independent_reference_minutes": reference,
            "reference_sampling_scheme": scheme,
        }
    if not out:
        raise ValueError("no independent observation effort windows")
    return out


def _read_coverage(path: Path, effort: dict) -> dict:
    """Verify interval-level joint exposure and two previously supplied totals."""
    by_stratum = defaultdict(list)
    all_by_site = defaultdict(list)
    seen_intervals = set()
    for row in _get_csv(path, REQUIRED_COVERAGE):
        key = _stratum(row)
        if key not in effort:
            raise ValueError("coverage interval has no corresponding effort stratum")
        interval_id = row["interval_id"].strip()
        reference_source = row["reference_source_id"].strip()
        if not interval_id or not reference_source or interval_id in seen_intervals:
            raise ValueError("missing or duplicate reference coverage interval identity")
        seen_intervals.add(interval_id)
        cs = _aware(row["camera_start"], "camera_start")
        ce = _aware(row["camera_end"], "camera_end")
        rs = _aware(row["reference_start"], "reference_start")
        re = _aware(row["reference_end"], "reference_end")
        if len({v.utcoffset() for v in (cs,ce,rs,re)}) != 1:
            raise ValueError("coverage endpoints must share a constant timezone offset")
        _within_clock_window(cs,ce,key[2])
        _within_clock_window(rs,re,key[2])
        start, end = max(cs,rs), min(ce,re)
        if not start < end:
            raise ValueError("camera/reference have no positive overlap")
        entry = {
            "interval_id": interval_id,
            "source": reference_source,
            "start": start, "end": end,
            "camera_start": cs, "camera_end": ce,
        }
        by_stratum[key].append(entry)
        all_by_site[key[0]].append((cs,ce,key,interval_id))
    if not seen_intervals:
        raise ValueError("no real reference coverage intervals")
    for site, rows in all_by_site.items():
        rows.sort(key=lambda x: x[0])
        for left, right in zip(rows,rows[1:]):
            if right[0] < left[1]:
                raise ValueError("overlapping camera coverage intervals double-count exposure")
    for key, values in effort.items():
        windows = by_stratum.get(key, [])
        if not windows:
            raise ValueError("effort stratum has no independently timed reference coverage")
        camera_minutes = math.fsum(
            (x["camera_end"]-x["camera_start"]).total_seconds()/60
            for x in windows
        )
        joint_minutes = math.fsum(
            (x["end"]-x["start"]).total_seconds()/60
            for x in windows
        )
        if not math.isclose(camera_minutes,values["camera_operational_minutes"],
                            abs_tol=1e-4,rel_tol=1e-9):
            raise ValueError("camera effort minutes disagree with timed interval union")
        if not math.isclose(joint_minutes,values["independent_reference_minutes"],
                            abs_tol=1e-4,rel_tol=1e-9):
            raise ValueError("independent reference minutes disagree with timed overlap")
    return by_stratum


def _read_passages(path: Path, effort: dict, coverage: dict) -> tuple[dict, dict]:
    rows = _get_csv(path, REQUIRED_PASSAGES)
    seen_passages, seen_camera_events = set(), set()
    by_cell = defaultdict(Counter)
    for row in rows:
        key = _stratum(row)
        if key not in effort:
            raise ValueError(f"reference passage lacks independent effort stratum {key}")
        pass_id = row["independent_passage_id"].strip()
        ref_id = row["reference_source_id"].strip()
        animal = row["species"].strip()
        if not pass_id or not ref_id or not animal:
            raise ValueError("independent passage/site/source/taxon identity missing")
        cam_event_id = row["camera_event_id"].strip()
        if pass_id == cam_event_id or ref_id == cam_event_id:
            raise ValueError("reference identity reused as focal camera event identity")
        if pass_id in seen_passages:
            raise ValueError("duplicate independent reference passage identity")
        seen_passages.add(pass_id)
        timestamp = _aware(row["reference_timestamp"], "reference_timestamp")
        if _clock(timestamp.hour) != key[2]:
            raise ValueError("recorded clock bin contradicts timestamp")
        matching = [
            window for window in coverage[key]
            if window["source"] == ref_id
            and window["start"] <= timestamp < window["end"]
        ]
        if len(matching) != 1:
            raise ValueError("passage outside uniquely matched independent reference exposure interval")
        triggered = _binary(row["camera_triggered"], "camera_triggered")
        registered = _binary(row["species_registered"], "species_registered")
        if registered > triggered:
            raise ValueError("registration cannot occur without matching trigger")
        if triggered and not cam_event_id:
            raise ValueError("triggered reference passage requires unique matched camera event ID")
        if not triggered and cam_event_id:
            raise ValueError("untriggered reference passage cannot be assigned a camera event")
        if cam_event_id:
            if cam_event_id in seen_camera_events:
                raise ValueError("camera event matched to multiple independent passages")
            seen_camera_events.add(cam_event_id)
        record = by_cell[key + (animal,)]
        record["known_passages"] += 1
        record["camera_triggered_passages"] += triggered
        record["registered_passages"] += registered
    return by_cell, {
        "independent_passage_rows":len(rows),
        "unique_independent_passages":len(seen_passages),
        "unique_matched_camera_events":len(seen_camera_events),
    }


def audit(effort_file: Path, passage_file: Path, coverage_file: Path) -> dict:
    effort = _read_effort(effort_file)
    coverage = _read_coverage(coverage_file, effort)
    passages, integrity = _read_passages(passage_file, effort, coverage)
    strata = []
    for (site, phase, clock), item in sorted(effort.items()):
        taxa = sorted({key[3] for key in passages if key[:3] == (site, phase, clock)})
        measurements = []
        for species in taxa:
            n = passages[site,phase,clock,species]
            known = n["known_passages"]
            trig = n["camera_triggered_passages"]
            registered = n["registered_passages"]
            measurements.append({
                "species":species,
                "independent_reference_passages":known,
                "matched_trigger_passages":trig,
                "registered_species_passages":registered,
                "trigger_given_known_passage":trig/known,
                "registration_given_trigger":registered/trig if trig else None,
                "effective_detection_given_known_passage":registered/known,
                "independent_passage_rate_per_reference_hour":
                    known*60/item["independent_reference_minutes"],
                "registered_passage_rate_per_reference_hour":
                    registered*60/item["independent_reference_minutes"],
            })
        strata.append({
            "site_id":site, "phase":phase,"clock_bin":clock,
            "camera_operational_minutes":item["camera_operational_minutes"],
            "independent_reference_minutes":item["independent_reference_minutes"],
            "reference_sampling_scheme":item["reference_sampling_scheme"],
            "verified_coverage_intervals":len(coverage[site,phase,clock]),
            "species_calibration":measurements,
        })
    return {
        "schema_version":2,
        "status":"TIME_WINDOW_VERIFIED_CONDITIONAL_REFERENCE_PASSAGE_CALIBRATION",
        "source":{
            "reference_passage_rows":integrity["independent_passage_rows"],
            "unique_independent_passage_ids":integrity["unique_independent_passages"],
            "unique_camera_trigger_ids":integrity["unique_matched_camera_events"],
            "verified_reference_coverage_intervals":sum(map(len,coverage.values())),
            "independent_reference_exposure_timed_and_joined":True,
        },
        "strata":strata,
        "limits":{
            "actual_reference_passages_must_be_truly_independent_of_camera":True,
            "reference_video_false_negative_rate_not_identified_by_this_schema":True,
            "camera_trigger_match_time_tolerance_not_verified_by_this_schema":True,
            "reference_passage_rate_is_conditional_on_reference_zone_and_effort":True,
            "randomized_time_block_inclusion_weights_not_estimated":True,
            "seasonal_activity_change_is_not_inferred_from_events_alone":True,
            "no_camera_proprietary_detection_probability_claimed":True,
            "none_of_E4_E5_E7_E7C_reopened":True,
            "original_E5_G4_passed":False,
            "new_external_ecological_result":False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--effort",type=Path,required=True)
    p.add_argument("--reference-passages",type=Path,required=True)
    p.add_argument("--coverage-intervals",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args = p.parse_args()
    result = audit(args.effort,args.reference_passages,args.coverage_intervals)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "number_of_effort_strata":len(result["strata"]),
        "verified_coverage_intervals":result["source"]["verified_reference_coverage_intervals"],
        "independent_passages":result["source"]["unique_independent_passage_ids"],
        "cells_with_known_passages":sum(len(s["species_calibration"]) for s in result["strata"]),
    },sort_keys=True))


if __name__ == "__main__":
    main()
