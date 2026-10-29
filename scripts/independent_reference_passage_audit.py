#!/usr/bin/env python3
"""Independent reference-passage vs camera-detection audit.

A reusable *data contract*, not an E5 gate pass, data-driven camera model,
or a new E7/E7-C result. All numbers are conditional on reference-pass
enumeration being independent and sampling windows being preselected.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import json
import math
from pathlib import Path

SUPPORTED_WINDOWS = {"night", "midday"}
SAMPLING_SCHEMES = {"continuous_reference", "randomized_time_blocks"}
REQUIRED_EFFORT = {
    "site_id", "phase", "clock_bin", "camera_operational_minutes",
    "independent_reference_minutes", "reference_sampling_scheme",
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


def _read_effort(path: Path) -> dict[tuple[str, str, str], dict]:
    rows = _get_csv(path, REQUIRED_EFFORT)
    out = {}
    schemes = set()
    for row in rows:
        key = _stratum(row)
        if key in out:
            raise ValueError(f"duplicate effort stratum {key}")
        if row["reference_sampling_scheme"].strip() not in SAMPLING_SCHEMES:
            raise ValueError("independent reference cannot be selected by camera trigger")
        camera = _positive(row["camera_operational_minutes"], "camera_operational_minutes")
        reference = _positive(row["independent_reference_minutes"], "independent_reference_minutes")
        if reference > camera:
            raise ValueError("reference overlap exceeds camera operational exposure")
        scheme = row["reference_sampling_scheme"].strip()
        schemes.add(scheme)
        out[key] = {
            "camera_operational_minutes": camera,
            "independent_reference_minutes": reference,
            "reference_sampling_scheme": scheme,
        }
    if not out:
        raise ValueError("no independent observation effort windows")
    return out


def _read_passages(path: Path, effort: dict) -> dict:
    rows = _get_csv(path, REQUIRED_PASSAGES)
    seen_passages, seen_camera_events = set(), set()
    by_cell = defaultdict(lambda: Counter())
    for row in rows:
        key = _stratum(row)
        if key not in effort:
            raise ValueError(f"reference passage lacks independent effort stratum {key}")
        pass_id = row["independent_passage_id"].strip()
        ref_id = row["reference_source_id"].strip()
        animal = row["species"].strip()
        if not pass_id or not ref_id or not animal:
            raise ValueError("independent passage/site/source/taxon identity missing")
        # The reference source must be independent of the focal camera
        # system, and its passage ID must never be borrowed from camera ID.
        cam_event_id = row["camera_event_id"].strip()
        if pass_id == cam_event_id or ref_id == cam_event_id:
            raise ValueError("reference identity reused as focal camera event identity")
        if pass_id in seen_passages:
            raise ValueError("duplicate independent reference passage identity")
        seen_passages.add(pass_id)
        raw = row["reference_timestamp"].strip()
        try:
            timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("invalid reference timestamp") from None
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("reference timestamp must carry an explicit timezone")
        local_hour = timestamp.hour
        from_clock = ("night" if local_hour >= 21 or local_hour < 4
                      else "midday" if 10 <= local_hour < 16 else None)
        if from_clock != key[2]:
            raise ValueError("recorded clock bin contradicts timestamp")
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
    return by_cell, {"independent_passage_rows": len(rows),
                     "unique_independent_passages":len(seen_passages),
                     "unique_matched_camera_events":len(seen_camera_events)}


def audit(effort_file: Path, passage_file: Path) -> dict:
    efforts = _read_effort(effort_file)
    passages, integrity = _read_passages(passage_file, efforts)
    strata = []
    for (site, phase, clock), effort in sorted(efforts.items()):
        taxa = sorted({key[3] for key in passages if key[:3] == (site, phase, clock)})
        rows = []
        for species in taxa:
            n = passages[site,phase,clock,species]
            reference = n["known_passages"]
            trig = n["camera_triggered_passages"]
            registered = n["registered_passages"]
            rows.append({
                "species":species,
                "independent_reference_passages":reference,
                "matched_trigger_passages":trig,
                "registered_species_passages":registered,
                "trigger_given_known_passage":trig/reference,
                "registration_given_trigger":registered/trig if trig else None,
                "effective_detection_given_known_passage":registered/reference,
                "independent_passage_rate_per_reference_hour":
                    reference*60/effort["independent_reference_minutes"],
                "registered_passage_rate_per_reference_hour":
                    registered*60/effort["independent_reference_minutes"],
            })
        strata.append({"site_id":site, "phase":phase, "clock_bin":clock,
                       "camera_operational_minutes":effort["camera_operational_minutes"],
                       "independent_reference_minutes":effort["independent_reference_minutes"],
                       "reference_sampling_scheme":effort["reference_sampling_scheme"],
                       "species_calibration":rows})
    return {
        "schema_version":1,
        "status":"CONDITIONAL_REFERENCE_PASSAGE_CALIBRATION_DESCRIPTOR",
        "source":{
            "reference_passage_rows":integrity["independent_passage_rows"],
            "unique_independent_passage_ids":integrity["unique_independent_passages"],
            "unique_camera_trigger_ids":integrity["unique_matched_camera_events"],
            "predeclared_non_trigger_based_reference_exposure_required":True,
        },
        "strata":strata,
        "limits":{
            "actual_reference_passages_must_be_truly_independent_of_camera":True,
            "reference_video_false_negative_rate_not_identified_by_this_schema":True,
            "reference_passage_rate_is_conditional_on_reference_zone_and_effort":True,
            "seasonal_activity_change_is_not_inferred_from_events_alone":True,
            "no_camera_proprietary_detection_probability_claimed":True,
            "none_of_E4_E5_E7_E7C_reopened":True,
            "original_E5_G4_passed":False,
            "new_external_ecological_result":False,
        },
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--effort",type=Path,required=True)
    p.add_argument("--reference-passages",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(args.effort,args.reference_passages)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "number_of_effort_strata":len(result["strata"]),
        "independent_passages":result["source"]["unique_independent_passage_ids"],
        "cells_with_known_passages":sum(len(s["species_calibration"]) for s in result["strata"]),
    },sort_keys=True))


if __name__=="__main__":
    main()
