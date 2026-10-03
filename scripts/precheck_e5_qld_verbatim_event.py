#!/usr/bin/env python3
"""Response-blind metadata precheck of Queensland ALA verbatim Event extension."""
from __future__ import annotations

import argparse
import collections
import csv
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-ala-verbatim-event-response-blind-v1"
FORBIDDEN_FRAGMENTS = (
    "scientificname", "taxon", "occurrenceid", "individualcount",
    "occurrencestatus", "lifestage", "sex", "behavior", "organismid",
)
OUTPUT_RAW_CATEGORY_FIELDS = ("eventtype", "habitat", "samplingprotocol")


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(value: str | None) -> str:
    if not value:
        return ""
    return re.split(r"[/#]", str(value).strip())[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {r"\t": "\t", r"\n": "\n", r"\r": "\r", r"\r\n": "\r\n"}.get(value, value)


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


def _section(section: ET.Element) -> dict[str, object]:
    fields = {}
    for field in _children(section, "field"):
        if "index" in field.attrib:
            fields[int(field.attrib["index"])] = _term_tail(field.attrib.get("term"))
    ident = _first_child(section, "coreid")
    return {
        "row_type": str(section.attrib.get("rowType", "")),
        "file": _file_location(section),
        "encoding": str(section.attrib.get("encoding", "UTF-8")),
        "delimiter": _decode_sep(section.attrib.get("fieldsTerminatedBy"), "\t"),
        "quotechar": _decode_sep(section.attrib.get("fieldsEnclosedBy"), '"'),
        "ignore_header_lines": int(section.attrib.get("ignoreHeaderLines", "0") or 0),
        "fields": fields,
        "coreid_index": (
            int(ident.attrib["index"])
            if ident is not None and "index" in ident.attrib
            else None
        ),
    }


def _parse_date(raw: str) -> date:
    value = str(raw).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.fromisoformat(value[:10])


def _months_for_event_date(raw: str) -> set[str]:
    value = str(raw).strip()
    if not value:
        return set()
    pieces = value.split("/", 1)
    try:
        start = _parse_date(pieces[0])
        end = _parse_date(pieces[1]) if len(pieces) == 2 else start
    except Exception:
        return set()
    if end < start:
        return set()
    months = set()
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.add(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y += 1
            m = 1
    return months


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_counter(counter: collections.Counter[str], *, raw_limit: int = 30) -> dict[str, object]:
    values = {str(k): int(v) for k, v in sorted(counter.items()) if str(k)}
    if len(values) <= raw_limit:
        return {
            "distinct_nonempty_count": len(values),
            "values": values,
            "value_hashes": [],
        }
    return {
        "distinct_nonempty_count": len(values),
        "values": {},
        "value_hashes": sorted(_hash(k) for k in values),
    }


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland verbatim Event contract")

    firewall = contract["response_firewall"]
    for key in (
        "event_core_rows_read_authorized",
        "occurrence_extension_data_read_authorized",
        "verbatim_occurrence_rows_read_authorized",
        "multimedia_rows_read_authorized",
        "extended_measurement_rows_read_authorized",
        "eventremarks_values_may_be_retained",
        "eventremarks_values_may_be_reported",
        "species_or_taxon_value_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    raw_archive = archive_path.read_bytes()
    observed_sha = hashlib.sha256(raw_archive).hexdigest()
    if observed_sha != contract["source"]["archive_sha256"]:
        raise ValueError("archive SHA256 drift")

    with zipfile.ZipFile(io.BytesIO(raw_archive)) as archive:
        names = set(archive.namelist())
        meta_name = contract["source"]["meta_xml_member"]
        if meta_name not in names:
            raise ValueError("meta.xml missing")
        root = ET.fromstring(archive.read(meta_name))

        matches = []
        for ext in _children(root, "extension"):
            spec = _section(ext)
            if (
                spec["file"] == contract["source"]["extension_file"]
                and spec["row_type"] == contract["source"]["extension_row_type"]
            ):
                matches.append(spec)
        if len(matches) != 1:
            raise ValueError(f"expected one pinned VerbatimEvent extension, got {len(matches)}")
        spec = matches[0]

        declared = sorted(set(spec["fields"].values()))
        expected = sorted(contract["expected_declared_terms"])
        if declared != expected:
            raise ValueError(f"VerbatimEvent schema drift: {declared!r}")

        forbidden_declared = sorted(
            term for term in declared
            if any(fragment in term for fragment in FORBIDDEN_FRAGMENTS)
        )
        if forbidden_declared:
            raise ValueError(f"response-bearing term declared in VerbatimEvent: {forbidden_declared!r}")

        authorized = set(contract["fields_authorized_for_values"])
        forbidden_values = set(contract["fields_declared_but_value_read_forbidden"])
        if authorized & forbidden_values:
            raise ValueError("authorized and forbidden value fields overlap")

        index_by_term = {
            term: index for index, term in spec["fields"].items() if term in authorized
        }
        extension_file = str(spec["file"])
        if extension_file not in names:
            raise ValueError("verbatim Event file missing")

        text = archive.read(extension_file).decode(
            str(spec["encoding"] or "UTF-8"), errors="strict"
        )

    handle = io.StringIO(text)
    for _ in range(int(spec["ignore_header_lines"])):
        next(handle, None)
    reader = csv.reader(
        handle,
        delimiter=str(spec["delimiter"]),
        quotechar=str(spec["quotechar"] or '"'),
    )

    max_index = max(list(spec["fields"]) + ([int(spec["coreid_index"])] if spec["coreid_index"] is not None else []))

    row_count = 0
    invalid_width = 0
    event_ids: set[str] = set()
    parent_ids: set[str] = set()
    coordinate_pairs: set[tuple[str, str]] = set()
    localities: set[str] = set()
    months: set[str] = set()
    parseable_date_rows = 0

    counters = {
        "eventtype": collections.Counter(),
        "habitat": collections.Counter(),
        "samplingprotocol": collections.Counter(),
        "samplingeffort": collections.Counter(),
        "deploymentgroups": collections.Counter(),
    }
    group_habitats: dict[str, set[str]] = collections.defaultdict(set)
    group_protocols: dict[str, set[str]] = collections.defaultdict(set)
    group_coordinates: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)

    def get(cells: list[str], term: str) -> str:
        index = index_by_term.get(term)
        return str(cells[index]).strip() if index is not None else ""

    for cells in reader:
        if not cells or not any(str(v).strip() for v in cells):
            continue
        if len(cells) <= max_index:
            invalid_width += 1
            continue

        row_count += 1
        event_id = get(cells, "eventid")
        parent_id = get(cells, "parenteventid")
        lat = get(cells, "decimallatitude")
        lon = get(cells, "decimallongitude")
        locality = get(cells, "locality")
        event_date = get(cells, "eventdate")
        event_type = get(cells, "eventtype")
        habitat = get(cells, "habitat")
        protocol = get(cells, "samplingprotocol")
        effort = get(cells, "samplingeffort")
        group = get(cells, "deploymentgroups")

        if event_id:
            event_ids.add(event_id)
        if parent_id:
            parent_ids.add(parent_id)
        if lat and lon:
            coordinate_pairs.add((lat, lon))
        if locality:
            localities.add(locality)
        if event_date:
            parsed = _months_for_event_date(event_date)
            if parsed:
                parseable_date_rows += 1
                months.update(parsed)

        if event_type:
            counters["eventtype"][event_type] += 1
        if habitat:
            counters["habitat"][habitat] += 1
        if protocol:
            counters["samplingprotocol"][protocol] += 1
        if effort:
            counters["samplingeffort"][effort] += 1
        if group:
            counters["deploymentgroups"][group] += 1
            if habitat:
                group_habitats[group].add(habitat)
            if protocol:
                group_protocols[group].add(protocol)
            if lat and lon:
                group_coordinates[group].add((lat, lon))

    group_sizes = collections.Counter(counters["deploymentgroups"].values())
    groups_with_multiple_rows = sum(v >= 2 for v in counters["deploymentgroups"].values())
    groups_with_multiple_habitats = sum(len(v) >= 2 for v in group_habitats.values())
    groups_with_multiple_protocols = sum(len(v) >= 2 for v in group_protocols.values())
    groups_with_multiple_coordinates = sum(len(v) >= 2 for v in group_coordinates.values())

    event_component_ok = (
        row_count > 0
        and parseable_date_rows > 0
        and len(event_ids) > 0
        and (len(coordinate_pairs) > 0 or len(localities) > 0)
    )
    crossed_pair_hint = (
        groups_with_multiple_rows >= 10
        and (groups_with_multiple_habitats >= 10 or groups_with_multiple_protocols >= 10)
    )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-ala-verbatim-event-precheck-v1",
        "status": "E5_RESPONSE_BLIND_QLD_VERBATIM_EVENT_PRECHECK",
        "source": {
            "archive_url": contract["source"]["archive_url"],
            "archive_sha256": observed_sha,
            "extension_file": extension_file,
            "extension_row_type": spec["row_type"],
            "declared_terms": declared,
        },
        "geometry": {
            "row_count": row_count,
            "invalid_width_rows": invalid_width,
            "unique_event_ids": len(event_ids),
            "unique_parent_event_ids": len(parent_ids),
            "unique_coordinate_pairs": len(coordinate_pairs),
            "unique_localities": len(localities),
            "parseable_eventdate_rows": parseable_date_rows,
            "distinct_calendar_months": sorted(months),
            "distinct_calendar_month_count": len(months),
        },
        "categories": {
            "event_type": _safe_counter(counters["eventtype"]),
            "habitat": _safe_counter(counters["habitat"]),
            "sampling_protocol": _safe_counter(counters["samplingprotocol"]),
            "sampling_effort": _safe_counter(counters["samplingeffort"], raw_limit=10),
        },
        "deployment_group_geometry": {
            "unique_nonempty_groups": len(counters["deploymentgroups"]),
            "rows_in_nonempty_groups": int(sum(counters["deploymentgroups"].values())),
            "group_size_histogram": {
                str(size): int(count) for size, count in sorted(group_sizes.items())
            },
            "groups_with_multiple_rows": groups_with_multiple_rows,
            "groups_with_multiple_habitat_values": groups_with_multiple_habitats,
            "groups_with_multiple_protocol_values": groups_with_multiple_protocols,
            "groups_with_multiple_coordinate_pairs": groups_with_multiple_coordinates,
            "max_group_size": max(counters["deploymentgroups"].values(), default=0),
            "raw_group_values_reported": False,
        },
        "capacity_hints": {
            "G2_event_metadata_component": "POTENTIAL" if event_component_ok else "INSUFFICIENT",
            "G3_matched_protocol_group_component": (
                "POTENTIAL_CROSSED_GEOMETRY" if crossed_pair_hint else "NOT_DEMONSTRATED"
            ),
            "G5_global_physical_location_capacity": (
                len(localities) >= 30
                or len(coordinate_pairs) >= 30
                or len(counters["deploymentgroups"]) >= 30
            ),
            "G6_global_six_month_capacity": len(months) >= 6,
        },
        "response_boundary": {
            "event_core_rows_read": 0,
            "verbatim_event_rows_read": row_count,
            "eventremarks_values_retained": 0,
            "eventremarks_values_reported": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
            "extended_measurement_rows_read": 0,
            "species_or_taxon_values_read": 0,
            "focal_response_opened": False,
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
            "separate_detection_identifiability_contract_required": True,
            "separate_split_contract_required": True,
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
