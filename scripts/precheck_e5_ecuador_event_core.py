#!/usr/bin/env python3
"""Response-blind E5 precheck for the Ecuador sampling-event DwC-A.

The occurrence extension is identified from meta.xml but never opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


FORBIDDEN_SUFFIXES = {
    "occurrenceID",
    "scientificName",
    "taxonID",
    "acceptedNameUsageID",
    "organismID",
    "organismQuantity",
    "organismQuantityType",
    "individualCount",
    "occurrenceStatus",
    "sex",
    "lifeStage",
    "behavior",
}


def _suffix(term: str) -> str:
    value = str(term).rstrip("/")
    return value.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _decode_sep(value: str | None, default: str) -> str:
    if value is None:
        return default
    return bytes(value, "utf-8").decode("unicode_escape")


def _descriptor(node: ET.Element) -> dict:
    locations = [
        grandchild.text.strip()
        for child in node
        if child.tag.endswith("files")
        for grandchild in child
        if grandchild.tag.endswith("location") and grandchild.text
    ]
    fields = []
    for child in node:
        if child.tag.endswith("field"):
            fields.append({
                "index": int(child.attrib["index"]),
                "term": child.attrib["term"],
                "suffix": _suffix(child.attrib["term"]),
            })
    id_index = None
    for child in node:
        if child.tag.endswith("id"):
            id_index = int(child.attrib["index"])
            break
    return {
        "row_type": node.attrib.get("rowType"),
        "locations": locations,
        "fields": sorted(fields, key=lambda row: row["index"]),
        "id_index": id_index,
        "encoding": node.attrib.get("encoding", "UTF-8"),
        "field_sep": _decode_sep(node.attrib.get("fieldsTerminatedBy"), "\t"),
        "line_sep": _decode_sep(node.attrib.get("linesTerminatedBy"), "\n"),
        "ignore_header_lines": int(node.attrib.get("ignoreHeaderLines", "0")),
    }


def _first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = str(row.get(name, "")).strip()
        if value:
            return value
    return ""


def _parse_date(value: str):
    from datetime import datetime
    text = str(value).strip()
    if not text:
        return None
    # Darwin Core eventDate can be an interval. For metadata support, retain
    # both interval endpoints as calendar support.
    values = text.split("/", 1)
    parsed = []
    for item in values:
        item = item.strip()
        if not item:
            continue
        if item.endswith("Z"):
            item = item[:-1] + "+00:00"
        try:
            parsed.append(datetime.fromisoformat(item))
        except ValueError:
            try:
                parsed.append(datetime.strptime(item[:10], "%Y-%m-%d"))
            except ValueError:
                pass
    return parsed


def precheck(archive_path: Path) -> dict:
    archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        names = sorted(archive.namelist())
        meta_names = [name for name in names if Path(name).name == "meta.xml"]
        if len(meta_names) != 1:
            raise ValueError(f"expected exactly one meta.xml, got {meta_names!r}")
        root = ET.fromstring(archive.read(meta_names[0]))

        core_nodes = [node for node in root if node.tag.endswith("core")]
        if len(core_nodes) != 1:
            raise ValueError("DwC-A must contain exactly one core")
        core = _descriptor(core_nodes[0])
        if not str(core["row_type"]).endswith("Event"):
            raise ValueError(f"core rowType must be Event, got {core['row_type']!r}")
        if len(core["locations"]) != 1:
            raise ValueError("Event core must have exactly one file location")

        extensions = [
            _descriptor(node) for node in root if node.tag.endswith("extension")
        ]
        occurrence = [
            item for item in extensions
            if str(item["row_type"]).endswith("Occurrence")
        ]
        if len(occurrence) != 1:
            raise ValueError("expected exactly one Occurrence extension descriptor")

        forbidden = sorted(
            {
                field["suffix"]
                for field in core["fields"]
                if field["suffix"] in FORBIDDEN_SUFFIXES
            }
        )
        if forbidden:
            raise ValueError(
                "Event core contains forbidden response-bearing terms: "
                + ", ".join(forbidden)
            )

        event_file = core["locations"][0]
        if event_file not in names:
            raise ValueError(f"Event core file missing: {event_file}")
        occurrence_files = tuple(occurrence[0]["locations"])
        if not occurrence_files:
            raise ValueError("Occurrence extension file location is absent")
        if any(name not in names for name in occurrence_files):
            raise ValueError("Occurrence extension file declared but missing")

        # Safety boundary: no archive.read() call is made for any occurrence file.
        raw = archive.read(event_file)

    encoding = str(core["encoding"])
    text = raw.decode(encoding)
    reader = csv.reader(io.StringIO(text), delimiter=str(core["field_sep"]))
    rows_raw = list(reader)
    ignore = int(core["ignore_header_lines"])
    rows_raw = rows_raw[ignore:]

    fields = core["fields"]
    index_to_suffix = {int(field["index"]): str(field["suffix"]) for field in fields}
    if core["id_index"] is not None and int(core["id_index"]) not in index_to_suffix:
        index_to_suffix[int(core["id_index"])] = "core_id"

    records = []
    for row_index, values in enumerate(rows_raw):
        if not values or not any(str(value).strip() for value in values):
            continue
        mapped = {
            suffix: (values[index] if index < len(values) else "")
            for index, suffix in index_to_suffix.items()
        }
        mapped["_row_index"] = str(row_index)
        records.append(mapped)

    event_ids = [
        _first_value(row, "eventID", "core_id") for row in records
    ]
    parent_ids = [_first_value(row, "parentEventID") for row in records]
    location_ids = [
        _first_value(row, "locationID", "locality") for row in records
    ]

    date_values = []
    months = set()
    for row in records:
        for name in ("eventDate", "startDayOfYear", "year"):
            value = _first_value(row, name)
            if name == "eventDate" and value:
                parsed = _parse_date(value) or []
                date_values.extend(parsed)
                months.update((item.year, item.month) for item in parsed)
                break

    lats = []
    lons = []
    for row in records:
        try:
            lat = float(_first_value(row, "decimalLatitude"))
            lon = float(_first_value(row, "decimalLongitude"))
        except ValueError:
            continue
        if math.isfinite(lat) and math.isfinite(lon):
            lats.append(lat)
            lons.append(lon)

    protocol_values = sorted(
        {
            _first_value(row, "samplingProtocol")
            for row in records
            if _first_value(row, "samplingProtocol")
        }
    )
    sample_size_units = sorted(
        {
            _first_value(row, "sampleSizeUnit")
            for row in records
            if _first_value(row, "sampleSizeUnit")
        }
    )
    geographic_labels = {}
    for field in ("country", "stateProvince", "county", "municipality", "locality"):
        values = {
            _first_value(row, field)
            for row in records
            if _first_value(row, field)
        }
        if values:
            geographic_labels[field] = {
                "unique_count": len(values),
                "values": sorted(values)[:50],
                "truncated": len(values) > 50,
            }

    distinct_locations = {value for value in location_ids if value}
    nonempty_events = [value for value in event_ids if value]
    result = {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "precheck_id": "e5-ecuador-event-core-only-precheck-v1",
        "status": "E5_METADATA_EVENT_CORE_PRECHECK_COMPLETE",
        "source": {
            "archive_sha256": archive_sha,
            "archive_member_names": names,
            "event_core_file": event_file,
            "occurrence_extension_files_present_but_unread": list(occurrence_files),
        },
        "response_boundary": {
            "meta_xml_read": True,
            "event_core_rows_read": len(records),
            "occurrence_extension_files_opened": False,
            "occurrence_extension_rows_read": 0,
            "focal_taxon_response_opened": False,
        },
        "event_core_schema": {
            "row_type": core["row_type"],
            "field_terms": [
                {"index": field["index"], "term": field["term"], "suffix": field["suffix"]}
                for field in fields
            ],
            "forbidden_response_terms_found": forbidden,
        },
        "geometry": {
            "event_core_row_count": len(records),
            "nonempty_event_id_count": len(nonempty_events),
            "unique_event_id_count": len(set(nonempty_events)),
            "duplicate_nonempty_event_id_count": (
                len(nonempty_events) - len(set(nonempty_events))
            ),
            "nonempty_parent_event_id_count": sum(bool(value) for value in parent_ids),
            "nonempty_location_id_or_locality_count": sum(
                bool(value) for value in location_ids
            ),
            "unique_location_id_or_locality_count": len(distinct_locations),
            "latitude_complete_rows": len(lats),
            "longitude_complete_rows": len(lons),
            "latitude_range": [min(lats), max(lats)] if lats else None,
            "longitude_range": [min(lons), max(lons)] if lons else None,
            "geographic_labels": geographic_labels,
        },
        "temporal_support": {
            "eventDate_parsed_value_count": len(date_values),
            "minimum_datetime": (
                min(date_values).isoformat() if date_values else None
            ),
            "maximum_datetime": (
                max(date_values).isoformat() if date_values else None
            ),
            "distinct_year_month_count": len(months),
            "year_months": [f"{year:04d}-{month:02d}" for year, month in sorted(months)],
            "overall_six_month_capacity_hint": len(months) >= 6,
            "final_train_holdout_G6_pass_authorized": False,
        },
        "effort_and_protocol": {
            "sampling_protocol_values": protocol_values,
            "sample_size_units": sample_size_units,
            "has_sample_size_value_field": any(
                field["suffix"] == "sampleSizeValue" for field in fields
            ),
            "has_sample_size_unit_field": any(
                field["suffix"] == "sampleSizeUnit" for field in fields
            ),
        },
        "preliminary_gate_hints": {
            "G1_INDEPENDENT_SOURCE": "PASS_PUBLIC_PROVENANCE",
            "G2_SCHEMA_EFFORT_TIME": (
                "PARTIAL_EVENT_CORE_METADATA_PASS_RESPONSE_SCHEMA_UNOPENED"
                if records and nonempty_events else
                "FAIL_OR_INCOMPLETE_EVENT_CORE_METADATA"
            ),
            "G3_CROSSED_DOMAIN": "MANUAL_GEOGRAPHY_SOURCE_REVIEW_REQUIRED",
            "G4_DETECTION_IDENTIFIABILITY": "NOT_ESTABLISHED_BY_EVENT_CORE_PRECHECK",
            "G5_PHYSICAL_REPLICATION": (
                "POTENTIAL" if len(distinct_locations) >= 30 else "INSUFFICIENT_OR_UNKNOWN"
            ),
            "G6_TEMPORAL_SUPPORT": (
                "POTENTIAL" if len(months) >= 6 else "NO_6_MONTH_OVERALL_SUPPORT"
            ),
            "G7_MODEL_FREEZE": "NOT_REACHED",
        },
        "decision_boundary": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "occurrence_extension_read_authorized": False,
            "separate_followup_contract_required": True,
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = precheck(args.archive)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "event_core_rows": result["geometry"]["event_core_row_count"],
        "occurrence_rows_read": result["response_boundary"]["occurrence_extension_rows_read"],
        "unique_locations": result["geometry"]["unique_location_id_or_locality_count"],
        "distinct_year_months": result["temporal_support"]["distinct_year_month_count"],
        "G4": result["preliminary_gate_hints"]["G4_DETECTION_IDENTIFIABILITY"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
