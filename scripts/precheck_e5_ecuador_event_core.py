#!/usr/bin/env python3
"""Response-blind E5 precheck for the Ecuador landscape-camera DwC-A.

The biological Occurrence extension is NEVER opened. Only meta.xml and the Event
core declared by meta.xml may be read. The result is a design/schema precheck and
cannot qualify E5 or authorize response opening.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-ecuador-event-core-response-blind-precheck-v1"
EXPECTED_EVENT_ROWS = 958

FORBIDDEN_CORE_TERM_FRAGMENTS = (
    "scientificname",
    "taxon",
    "occurrenceid",
    "individualcount",
    "occurrencestatus",
    "lifestage",
    "sex",
    "behavior",
    "organismid",
)

SAFE_EVENT_TERMS = {
    "eventid",
    "parenteventid",
    "locationid",
    "eventdate",
    "verbatimeventdate",
    "samplingprotocol",
    "samplingeffort",
    "decimallatitude",
    "decimallongitude",
    "locality",
    "habitat",
    "country",
    "countrycode",
    "stateprovince",
    "county",
    "municipality",
    "fieldnumber",
    "samplesizevalue",
    "samplesizeunit",
    "year",
    "month",
    "day",
}


def _local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(term: str | None) -> str:
    if not term:
        return ""
    return re.split(r"[/#]", str(term).strip())[-1].lower()


def _decode_separator(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    mapping = {
        r"\t": "\t",
        r"\n": "\n",
        r"\r": "\r",
        r"\r\n": "\r\n",
    }
    return mapping.get(value, value)


def _first_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child
    return None


def _all_children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _file_location(section: ET.Element) -> str:
    files = _first_child(section, "files")
    if files is None:
        raise ValueError("DwC section is missing files")
    location = _first_child(files, "location")
    if location is None or not (location.text or "").strip():
        raise ValueError("DwC section is missing file location")
    return str(location.text).strip()


def _field_schema(section: ET.Element) -> dict[int, str]:
    output: dict[int, str] = {}
    for field in _all_children(section, "field"):
        if "index" not in field.attrib:
            continue
        output[int(field.attrib["index"])] = _term_tail(field.attrib.get("term"))
    return output


def _core_id_index(section: ET.Element) -> int | None:
    ident = _first_child(section, "id")
    if ident is None or "index" not in ident.attrib:
        return None
    return int(ident.attrib["index"])


def _extension_coreid_index(section: ET.Element) -> int | None:
    ident = _first_child(section, "coreid")
    if ident is None or "index" not in ident.attrib:
        return None
    return int(ident.attrib["index"])


def _section_spec(section: ET.Element) -> dict[str, object]:
    return {
        "row_type": str(section.attrib.get("rowType", "")),
        "file": _file_location(section),
        "encoding": str(section.attrib.get("encoding", "UTF-8")),
        "delimiter": _decode_separator(section.attrib.get("fieldsTerminatedBy"), "\t"),
        "quotechar": _decode_separator(section.attrib.get("fieldsEnclosedBy"), '"'),
        "ignore_header_lines": int(section.attrib.get("ignoreHeaderLines", "0") or 0),
        "fields": _field_schema(section),
        "id_index": _core_id_index(section),
        "coreid_index": _extension_coreid_index(section),
    }


def _parse_date(value: str) -> date:
    raw = str(value).strip()
    if not raw:
        raise ValueError("empty date")
    raw = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return date.fromisoformat(raw[:10])


def _months_between(start: date, end: date) -> set[str]:
    if end < start:
        raise ValueError("date interval ends before it starts")
    year, month = start.year, start.month
    out: set[str] = set()
    while (year, month) <= (end.year, end.month):
        out.add(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return out


def _event_months(value: str) -> set[str]:
    raw = str(value).strip()
    if not raw:
        return set()
    pieces = raw.split("/", 1)
    try:
        start = _parse_date(pieces[0])
        end = _parse_date(pieces[1]) if len(pieces) == 2 else start
    except ValueError:
        # Fail closed for the temporal-support hint but do not expose raw values.
        return set()
    return _months_between(start, end)


def _read_event_core(
    archive: zipfile.ZipFile,
    spec: dict[str, object],
) -> tuple[list[dict[str, str]], dict[str, object]]:
    fields = dict(spec["fields"])
    sensitive = sorted(
        term
        for term in fields.values()
        if any(fragment in term for fragment in FORBIDDEN_CORE_TERM_FRAGMENTS)
    )
    if sensitive:
        raise ValueError(
            "Event core declares response-bearing/taxonomic fields and cannot be "
            f"opened under the response-blind contract: {sensitive!r}"
        )

    member = str(spec["file"])
    encoding = str(spec["encoding"] or "UTF-8")
    delimiter = str(spec["delimiter"])
    quotechar = str(spec["quotechar"])
    ignore = int(spec["ignore_header_lines"])

    raw = archive.read(member)
    text = raw.decode(encoding, errors="strict")
    handle = io.StringIO(text)
    for _ in range(ignore):
        next(handle, None)
    reader = csv.reader(handle, delimiter=delimiter, quotechar=quotechar or '"')

    rows: list[dict[str, str]] = []
    invalid_width = 0
    max_index = max(
        list(fields) + ([int(spec["id_index"])] if spec["id_index"] is not None else [])
    )
    for cells in reader:
        if not cells or not any(str(value).strip() for value in cells):
            continue
        if len(cells) <= max_index:
            invalid_width += 1
            continue
        row: dict[str, str] = {}
        if spec["id_index"] is not None:
            row["core_id"] = str(cells[int(spec["id_index"])]).strip()
        for index, term in fields.items():
            if term in SAFE_EVENT_TERMS:
                row[term] = str(cells[index]).strip()
        rows.append(row)

    return rows, {
        "invalid_width_rows": invalid_width,
        "core_declared_terms": sorted(set(fields.values())),
        "safe_terms_read": sorted(
            {term for term in fields.values() if term in SAFE_EVENT_TERMS}
        ),
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Ecuador precheck contract")
    firewall = contract["response_firewall"]
    if firewall.get("occurrence_extension_data_read_authorized") is not False:
        raise ValueError("Occurrence extension must remain forbidden")
    if int(firewall.get("expected_occurrence_rows_read", -1)) != 0:
        raise ValueError("Occurrence row-read boundary drifted")

    archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive_path) as archive:
        members = sorted(
            name for name in archive.namelist() if not name.endswith("/")
        )
        meta_candidates = [
            name for name in members
            if PurePosixPath(name).name.lower() == "meta.xml"
        ]
        if len(meta_candidates) != 1:
            raise ValueError(f"expected exactly one meta.xml, got {meta_candidates!r}")
        meta_member = meta_candidates[0]
        root = ET.fromstring(archive.read(meta_member))

        core_sections = [
            child for child in root if _local_name(child.tag) == "core"
        ]
        if len(core_sections) != 1:
            raise ValueError("expected exactly one DwC core")
        core_spec = _section_spec(core_sections[0])

        extension_specs = [
            _section_spec(child)
            for child in root
            if _local_name(child.tag) == "extension"
        ]
        occurrence_specs = [
            spec for spec in extension_specs
            if str(spec["row_type"]).rstrip("/").lower().endswith("occurrence")
        ]
        if len(occurrence_specs) != 1:
            raise ValueError(
                f"expected exactly one Occurrence extension, got {len(occurrence_specs)}"
            )
        occurrence_spec = occurrence_specs[0]

        core_file = str(core_spec["file"])
        occurrence_file = str(occurrence_spec["file"])
        if core_file == occurrence_file:
            raise ValueError("Event core and Occurrence extension resolve to same file")

        rows, core_audit = _read_event_core(archive, core_spec)

    if len(rows) != EXPECTED_EVENT_ROWS:
        raise ValueError(
            f"Event core row count drifted: {len(rows)} != {EXPECTED_EVENT_ROWS}"
        )

    occurrence_terms = sorted(set(dict(occurrence_spec["fields"]).values()))
    occurrence_required_schema = {
        "taxon_identity_declared": any(
            term in occurrence_terms
            for term in ("scientificname", "taxonid", "acceptednameusage")
        ),
        "event_link_declared": (
            occurrence_spec["coreid_index"] is not None
            or "eventid" in occurrence_terms
        ),
        "event_time_term_declared": any(
            term in occurrence_terms for term in ("eventdate", "eventtime")
        ),
        "occurrence_id_declared": "occurrenceid" in occurrence_terms,
    }

    event_terms = set(core_audit["safe_terms_read"])
    location_ids = {
        row.get("locationid", "").strip()
        for row in rows
        if row.get("locationid", "").strip()
    }
    coordinate_pairs = {
        (row.get("decimallatitude", "").strip(), row.get("decimallongitude", "").strip())
        for row in rows
        if row.get("decimallatitude", "").strip()
        and row.get("decimallongitude", "").strip()
    }
    core_ids = {
        row.get("core_id", "").strip()
        for row in rows
        if row.get("core_id", "").strip()
    }

    if location_ids:
        physical_key = "locationID"
        physical_values = location_ids
        key_for_row = lambda row: row.get("locationid", "").strip()
    elif coordinate_pairs:
        physical_key = "decimalLatitude+decimalLongitude"
        physical_values = coordinate_pairs
        key_for_row = lambda row: (
            row.get("decimallatitude", "").strip(),
            row.get("decimallongitude", "").strip(),
        )
    else:
        physical_key = None
        physical_values = set()
        key_for_row = lambda row: None

    visits: dict[object, int] = {}
    for row in rows:
        key = key_for_row(row)
        if key and key != ("", ""):
            visits[key] = visits.get(key, 0) + 1
    repeated_locations = sum(value >= 2 for value in visits.values())

    months: set[str] = set()
    date_rows_nonempty = 0
    date_rows_parseable = 0
    for row in rows:
        value = row.get("eventdate", "").strip()
        if not value:
            continue
        date_rows_nonempty += 1
        parsed = _event_months(value)
        if parsed:
            date_rows_parseable += 1
            months.update(parsed)

    sampling_protocol_nonempty = sum(
        bool(row.get("samplingprotocol", "").strip()) for row in rows
    )
    sampling_effort_nonempty = sum(
        bool(row.get("samplingeffort", "").strip()) for row in rows
    )
    parent_event_nonempty = sum(
        bool(row.get("parenteventid", "").strip()) for row in rows
    )

    deployment_schema_ok = (
        physical_key is not None
        and "eventdate" in event_terms
        and (
            "samplingprotocol" in event_terms
            or "samplingeffort" in event_terms
        )
        and date_rows_nonempty > 0
        and date_rows_parseable == date_rows_nonempty
    )
    occurrence_schema_ok = (
        occurrence_required_schema["taxon_identity_declared"]
        and occurrence_required_schema["event_link_declared"]
    )

    g2 = (
        "PARTIAL_EVENT_CORE_AND_OCCURRENCE_SCHEMA_PASS_VALUES_UNVERIFIED"
        if deployment_schema_ok and occurrence_schema_ok
        else "FAIL_OR_INCOMPLETE_RESPONSE_BLIND_SCHEMA"
    )
    g4 = (
        "POTENTIAL_REPEAT_VISIT_PATH_MANUAL_IDENTIFIABILITY_REVIEW_REQUIRED"
        if repeated_locations >= 1 or parent_event_nonempty >= 1
        else "NO_REPEAT_VISIT_GEOMETRY_OBSERVED"
    )
    g5 = (
        "POTENTIAL_LOCATION_COUNTS_ONLY_SPLIT_NOT_FROZEN"
        if len(physical_values) >= 30
        else "FAIL_OR_INSUFFICIENT_PHYSICAL_LOCATION_GEOMETRY"
    )
    g6 = (
        "POTENTIAL_MONTH_SUPPORT_ONLY_SPLIT_NOT_FROZEN"
        if len(months) >= 6
        else "FAIL_OR_INSUFFICIENT_GLOBAL_MONTH_SUPPORT"
    )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "ecuador_landscape_camera_2023",
        "precheck_id": "e5-ecuador-event-core-response-blind-precheck-result-v1",
        "status": "E5_RESPONSE_BLIND_EVENT_CORE_PRECHECK",
        "contract_id": EXPECTED_CONTRACT_ID,
        "archive_sha256": archive_sha,
        "response_boundary": {
            "meta_xml_opened": True,
            "event_core_opened": True,
            "eml_opened": False,
            "occurrence_extension_file": occurrence_file,
            "occurrence_extension_opened": False,
            "occurrence_rows_read": 0,
            "archive_uploaded_as_artifact": False,
            "event_core_raw_rows_uploaded_as_artifact": False,
        },
        "archive": {
            "member_names": members,
            "event_core_file": core_file,
            "event_core_row_count": len(rows),
            "occurrence_extension_declared": True,
            "occurrence_extension_row_type": occurrence_spec["row_type"],
        },
        "event_core_schema": {
            **core_audit,
            "physical_location_key_used_for_hint": physical_key,
            "core_id_unique_count": len(core_ids),
            "location_id_unique_count": len(location_ids),
            "coordinate_pair_unique_count": len(coordinate_pairs),
        },
        "occurrence_extension_schema_from_meta_xml_only": {
            "declared_terms": occurrence_terms,
            **occurrence_required_schema,
            "values_opened": False,
        },
        "event_core_geometry": {
            "physical_location_candidate_count": len(physical_values),
            "locations_with_two_or_more_event_rows": repeated_locations,
            "parent_event_id_nonempty_rows": parent_event_nonempty,
            "event_date_nonempty_rows": date_rows_nonempty,
            "event_date_parseable_rows": date_rows_parseable,
            "distinct_calendar_months": len(months),
            "calendar_months": sorted(months),
            "sampling_protocol_nonempty_rows": sampling_protocol_nonempty,
            "sampling_effort_nonempty_rows": sampling_effort_nonempty,
        },
        "preliminary_gate_hints": {
            "G1_INDEPENDENT_SOURCE": "PASS_FROM_PARENT_REGISTRY",
            "G2_SCHEMA_EFFORT_TIME": g2,
            "G3_CROSSED_DOMAIN": "MANUAL_REVIEW_REQUIRED",
            "G4_DETECTION_IDENTIFIABILITY": g4,
            "G5_PHYSICAL_REPLICATION": g5,
            "G6_TEMPORAL_SUPPORT": g6,
            "G7_MODEL_FREEZE": "NOT_REACHED",
        },
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "selected_candidate_contract_authorized": False,
            "next_step_if_promising": (
                "manual response-blind adjudication of geography/source crossing, "
                "repeat-visit detection identifiability, and a frozen physical-location "
                "training/heldout split before any Occurrence data opening"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = precheck(args.archive, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "event_core_rows": result["archive"]["event_core_row_count"],
        "occurrence_rows_read": result["response_boundary"]["occurrence_rows_read"],
        "physical_location_candidate_count": result["event_core_geometry"][
            "physical_location_candidate_count"
        ],
        "distinct_calendar_months": result["event_core_geometry"][
            "distinct_calendar_months"
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
