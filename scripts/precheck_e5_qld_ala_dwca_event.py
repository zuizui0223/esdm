#!/usr/bin/env python3
"""Response-blind Event-core precheck for the public Queensland ALA DwC-A."""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-ala-dwca-event-core-response-blind-v1"

FORBIDDEN_FRAGMENTS = (
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

SAFE_TERMS = {
    "eventid",
    "parenteventid",
    "locationid",
    "eventdate",
    "verbatimeventdate",
    "samplingprotocol",
    "samplingeffort",
    "samplesizevalue",
    "samplesizeunit",
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
    "year",
    "month",
    "day",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(term: str | None) -> str:
    if not term:
        return ""
    return re.split(r"[/#]", str(term).strip())[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {
        r"\t": "\t",
        r"\n": "\n",
        r"\r": "\r",
        r"\r\n": "\r\n",
    }.get(value, value)


def _first_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _local(child.tag) == name]


def _file_location(section: ET.Element) -> str:
    files = _first_child(section, "files")
    if files is None:
        raise ValueError("DwC section missing files")
    location = _first_child(files, "location")
    if location is None or not (location.text or "").strip():
        raise ValueError("DwC section missing file location")
    return str(location.text).strip()


def _field_schema(section: ET.Element) -> dict[int, str]:
    out: dict[int, str] = {}
    for field in _children(section, "field"):
        if "index" not in field.attrib:
            continue
        out[int(field.attrib["index"])] = _term_tail(field.attrib.get("term"))
    return out


def _section(section: ET.Element, *, kind: str) -> dict[str, object]:
    ident_name = "id" if kind == "core" else "coreid"
    ident = _first_child(section, ident_name)
    ident_index = (
        int(ident.attrib["index"])
        if ident is not None and "index" in ident.attrib
        else None
    )
    return {
        "kind": kind,
        "row_type": str(section.attrib.get("rowType", "")),
        "file": _file_location(section),
        "encoding": str(section.attrib.get("encoding", "UTF-8")),
        "delimiter": _decode_sep(section.attrib.get("fieldsTerminatedBy"), "\t"),
        "quotechar": _decode_sep(section.attrib.get("fieldsEnclosedBy"), '"'),
        "ignore_header_lines": int(section.attrib.get("ignoreHeaderLines", "0") or 0),
        "fields": _field_schema(section),
        "identity_index": ident_index,
    }


def _months_between(start: date, end: date) -> set[str]:
    if end < start:
        return set()
    y, m = start.year, start.month
    out = set()
    while (y, m) <= (end.year, end.month):
        out.add(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return out


def _parse_date(value: str) -> date:
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return date.fromisoformat(raw[:10])


def _event_months(value: str) -> set[str]:
    raw = str(value).strip()
    if not raw:
        return set()
    pieces = raw.split("/", 1)
    try:
        start = _parse_date(pieces[0])
        end = _parse_date(pieces[1]) if len(pieces) == 2 else start
    except Exception:
        return set()
    return _months_between(start, end)


def _hash_category(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_safe_core(archive: zipfile.ZipFile, spec: dict[str, object]) -> dict[str, object]:
    fields = dict(spec["fields"])
    forbidden = sorted(
        term
        for term in fields.values()
        if any(fragment in term for fragment in FORBIDDEN_FRAGMENTS)
    )
    if forbidden:
        return {
            "status": "SCHEMA_STOP_RESPONSE_BEARING_CORE",
            "forbidden_declared_terms": forbidden,
            "rows_read": 0,
        }

    member = str(spec["file"])
    if member not in archive.namelist():
        raise ValueError(f"declared core file missing: {member}")

    raw = archive.read(member)
    text = raw.decode(str(spec["encoding"] or "UTF-8"), errors="strict")
    handle = io.StringIO(text)
    for _ in range(int(spec["ignore_header_lines"])):
        next(handle, None)

    reader = csv.reader(
        handle,
        delimiter=str(spec["delimiter"]),
        quotechar=str(spec["quotechar"] or '"'),
    )

    max_index = max(
        list(fields)
        + (
            [int(spec["identity_index"])]
            if spec["identity_index"] is not None
            else []
        )
    )

    row_count = 0
    invalid_width = 0
    event_ids = set()
    parent_ids = set()
    location_ids = set()
    coordinate_pairs = set()
    months = set()
    parseable_eventdate_rows = 0
    protocol_values = set()
    effort_values = set()
    field_number_values = set()

    idx_for = {term: idx for idx, term in fields.items() if term in SAFE_TERMS}

    for cells in reader:
        if not cells or not any(str(v).strip() for v in cells):
            continue
        if len(cells) <= max_index:
            invalid_width += 1
            continue
        row_count += 1

        def get(term: str) -> str:
            idx = idx_for.get(term)
            return str(cells[idx]).strip() if idx is not None else ""

        event_id = get("eventid")
        parent = get("parenteventid")
        location = get("locationid")
        lat = get("decimallatitude")
        lon = get("decimallongitude")
        event_date = get("eventdate")
        protocol = get("samplingprotocol")
        effort = get("samplingeffort")
        field_number = get("fieldnumber")

        if event_id:
            event_ids.add(event_id)
        if parent:
            parent_ids.add(parent)
        if location:
            location_ids.add(location)
        if lat and lon:
            coordinate_pairs.add((lat, lon))
        if event_date:
            parsed = _event_months(event_date)
            if parsed:
                parseable_eventdate_rows += 1
                months.update(parsed)
        if protocol:
            protocol_values.add(protocol)
        if effort:
            effort_values.add(effort)
        if field_number:
            field_number_values.add(field_number)

    return {
        "status": "SAFE_EVENT_CORE_READ",
        "rows_read": row_count,
        "invalid_width_rows": invalid_width,
        "unique_event_ids": len(event_ids),
        "unique_parent_event_ids": len(parent_ids),
        "unique_location_ids": len(location_ids),
        "unique_coordinate_pairs": len(coordinate_pairs),
        "distinct_calendar_months": sorted(months),
        "distinct_calendar_month_count": len(months),
        "parseable_eventdate_rows": parseable_eventdate_rows,
        "sampling_protocol": {
            "distinct_nonempty_count": len(protocol_values),
            "value_hashes": sorted(_hash_category(v) for v in protocol_values),
        },
        "sampling_effort": {
            "distinct_nonempty_count": len(effort_values),
            "value_hashes": sorted(_hash_category(v) for v in effort_values),
        },
        "field_number": {
            "distinct_nonempty_count": len(field_number_values),
            "value_hashes": sorted(_hash_category(v) for v in field_number_values),
        },
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland ALA DwC-A contract")

    firewall = contract["response_firewall"]
    if firewall.get("occurrence_extension_data_read_authorized") is not False:
        raise ValueError("Occurrence extension must remain forbidden")
    if int(firewall.get("expected_occurrence_rows_read", -1)) != 0:
        raise ValueError("expected Occurrence rows must remain zero")
    for key in (
        "media_file_read_authorized",
        "species_or_taxon_value_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    archive_raw = archive_path.read_bytes()
    archive_sha = _sha256(archive_raw)

    with zipfile.ZipFile(io.BytesIO(archive_raw)) as archive:
        names = sorted(name for name in archive.namelist() if not name.endswith("/"))
        meta_candidates = [
            n for n in names if PurePosixPath(n).name.lower() == "meta.xml"
        ]
        if len(meta_candidates) != 1:
            raise ValueError(f"expected one meta.xml, got {meta_candidates!r}")

        meta_name = meta_candidates[0]
        meta_raw = archive.read(meta_name)
        root = ET.fromstring(meta_raw)

        core_elem = _first_child(root, "core")
        if core_elem is None:
            raise ValueError("DwC-A meta.xml missing core")
        core = _section(core_elem, kind="core")

        extensions = []
        for element in _children(root, "extension"):
            extensions.append(_section(element, kind="extension"))

        core_declared_terms = sorted(set(core["fields"].values()))
        extension_schemas = [
            {
                "row_type": item["row_type"],
                "file": item["file"],
                "declared_terms": sorted(set(item["fields"].values())),
            }
            for item in extensions
        ]

        safe = _read_safe_core(archive, core)

    status = (
        "E5_RESPONSE_BLIND_QLD_EVENT_CORE_PRECHECK"
        if safe["status"] == "SAFE_EVENT_CORE_READ"
        else "E5_RESPONSE_BLIND_QLD_EVENT_CORE_SCHEMA_STOP"
    )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-ala-dwca-event-core-precheck-v1",
        "status": status,
        "source": {
            "archive_url": contract["source"]["archive_url"],
            "archive_sha256": archive_sha,
            "archive_member_count": len(names),
            "archive_member_names": names,
            "meta_xml_member": meta_name,
        },
        "schema": {
            "core_row_type": core["row_type"],
            "core_file": core["file"],
            "core_declared_terms": core_declared_terms,
            "safe_core_terms_present": sorted(
                term for term in core_declared_terms if term in SAFE_TERMS
            ),
            "extensions": extension_schemas,
        },
        "event_core_summary": safe,
        "response_boundary": {
            "meta_xml_opened": True,
            "event_core_rows_read": int(safe.get("rows_read", 0)),
            "occurrence_extension_data_opened": False,
            "occurrence_rows_read": 0,
            "media_files_opened": 0,
            "species_or_taxon_values_read": 0,
            "focal_response_opened": False,
        },
        "capacity_hints": {
            "G2_event_component": (
                "POTENTIAL"
                if safe["status"] == "SAFE_EVENT_CORE_READ"
                else "SCHEMA_STOP"
            ),
            "G5_global_physical_location_capacity": (
                int(safe.get("unique_location_ids", 0)) >= 30
                or int(safe.get("unique_coordinate_pairs", 0)) >= 30
            ),
            "G6_global_six_month_capacity": int(
                safe.get("distinct_calendar_month_count", 0)
            ) >= 6,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "G5_pass_authorized": False,
            "G6_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_split_contract_required": True,
            "occurrence_extension_opening_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    value = precheck(args.archive, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
