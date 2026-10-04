#!/usr/bin/env python3
"""Response-blind Deployment metadata completeness diagnostic for E5 Queensland."""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-deployment-completeness-response-blind-v1"


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(term: str | None) -> str:
    if not term:
        return ""
    return str(term).strip().replace("#", "/").rsplit("/", 1)[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {r"\t": "\t", r"\n": "\n", r"\r": "\r", r"\r\n": "\r\n"}.get(value, value)


def _first_child(element: ET.Element, name: str):
    return next((c for c in element if _local(c.tag) == name), None)


def _section(root: ET.Element, filename: str) -> dict[str, object]:
    matches = []
    for child in root:
        if _local(child.tag) not in {"core", "extension"}:
            continue
        files = _first_child(child, "files")
        loc = _first_child(files, "location") if files is not None else None
        if loc is None or str(loc.text or "").strip() != filename:
            continue
        fields = {}
        for field in child:
            if _local(field.tag) == "field" and "index" in field.attrib:
                fields[int(field.attrib["index"])] = _term_tail(field.attrib.get("term"))
        matches.append({
            "file": filename,
            "encoding": str(child.attrib.get("encoding", "UTF-8")),
            "delimiter": _decode_sep(child.attrib.get("fieldsTerminatedBy"), "\t"),
            "quotechar": _decode_sep(child.attrib.get("fieldsEnclosedBy"), '"'),
            "ignore_header_lines": int(child.attrib.get("ignoreHeaderLines", "0") or 0),
            "fields": fields,
        })
    if len(matches) != 1:
        raise ValueError(f"expected exactly one section for {filename!r}, got {len(matches)}")
    return matches[0]


def _index(spec: dict[str, object], term: str) -> int:
    matches = [i for i, name in dict(spec["fields"]).items() if name == term]
    if len(matches) != 1:
        raise ValueError(f"expected one index for {term}: {matches}")
    return matches[0]


def _prefix_field_bytes(raw_line: bytes, delimiter: bytes, quote: bytes, max_index: int):
    fields = []
    current = bytearray()
    in_quotes = False
    i = 0
    while i < len(raw_line):
        b = raw_line[i:i+1]
        if b == quote:
            if in_quotes and i + 1 < len(raw_line) and raw_line[i+1:i+2] == quote:
                current.extend(quote)
                i += 2
                continue
            in_quotes = not in_quotes
            current.extend(b)
            i += 1
            continue
        if b == delimiter and not in_quotes:
            fields.append(bytes(current))
            current.clear()
            if len(fields) > max_index:
                return fields
            i += 1
            continue
        if b in {b"\n", b"\r"} and not in_quotes:
            break
        current.extend(b)
        i += 1
    fields.append(bytes(current))
    return fields


def _decode_field(raw: bytes, encoding: str, quote: bytes) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[:1] == quote and value[-1:] == quote:
        value = value[1:-1].replace(quote + quote, quote)
    return value.decode(encoding, errors="strict").strip()


def _parse_date(value: str) -> date:
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return date.fromisoformat(raw[:10])


def _interval(value: str) -> tuple[date, date]:
    raw = str(value).strip()
    if not raw:
        raise ValueError("empty")
    pieces = raw.split("/", 1)
    start = _parse_date(pieces[0])
    end = _parse_date(pieces[1]) if len(pieces) == 2 else start
    if end < start:
        raise ValueError("reversed")
    return start, end


def _months(start: date, end: date) -> set[str]:
    year, month = start.year, start.month
    out = set()
    while (year, month) <= (end.year, end.month):
        out.add(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return out


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland completeness contract")

    fw = contract["response_firewall"]
    for key in (
        "raw_eventid_report_authorized",
        "raw_eventdate_report_authorized",
        "raw_coordinates_report_authorized",
        "raw_locality_report_authorized",
        "eventremarks_value_decode_authorized",
        "event_core_rows_read_authorized",
        "emof_rows_read_authorized",
        "occurrence_rows_read_authorized",
        "verbatim_occurrence_rows_read_authorized",
        "multimedia_rows_read_authorized",
        "species_or_taxon_values_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    raw = archive_path.read_bytes()
    archive_sha = hashlib.sha256(raw).hexdigest()
    if archive_sha != contract["source"]["archive_sha256"]:
        raise ValueError("archive SHA256 drift")

    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        root = ET.fromstring(z.read(contract["source"]["meta_xml_member"]))
        spec = _section(root, contract["source"]["verbatim_event_file"])
        required_terms = (
            "eventid", "eventdate", "eventtype", "decimallatitude",
            "decimallongitude", "locality", "samplingprotocol",
        )
        indexes = {term: _index(spec, term) for term in required_terms}
        max_index = max(indexes.values())
        delimiter = str(spec["delimiter"]).encode()
        quote = str(spec["quotechar"] or '"').encode()
        if len(delimiter) != 1 or len(quote) != 1:
            raise ValueError("only single-byte delimiter/quote supported")
        encoding = str(spec["encoding"] or "UTF-8")

        counts = {
            "deployment_rows": 0,
            "missing_eventid": 0,
            "missing_eventdate": 0,
            "invalid_eventdate": 0,
            "missing_latitude": 0,
            "invalid_latitude": 0,
            "missing_longitude": 0,
            "invalid_longitude": 0,
            "missing_locality": 0,
            "missing_samplingprotocol": 0,
            "complete_case_rows": 0,
        }
        coordinates = set()
        all_months = set()
        locality = defaultdict(lambda: {"rows": 0, "coordinates": set(), "months": set()})

        with z.open(str(spec["file"]), "r") as stream:
            for _ in range(int(spec["ignore_header_lines"])):
                stream.readline()
            for raw_line in stream:
                if not raw_line.strip():
                    continue
                prefix = _prefix_field_bytes(raw_line, delimiter, quote, max_index)
                if len(prefix) <= max_index:
                    raise ValueError("cannot parse VerbatimEvent prefix")
                values = {
                    term: _decode_field(prefix[indexes[term]], encoding, quote)
                    for term in required_terms
                }
                if values["eventtype"].casefold() != "deployment":
                    continue

                counts["deployment_rows"] += 1
                if not values["eventid"]:
                    counts["missing_eventid"] += 1
                if not values["eventdate"]:
                    counts["missing_eventdate"] += 1
                    interval = None
                else:
                    try:
                        interval = _interval(values["eventdate"])
                    except ValueError:
                        counts["invalid_eventdate"] += 1
                        interval = None

                lat = None
                if not values["decimallatitude"]:
                    counts["missing_latitude"] += 1
                else:
                    try:
                        lat = float(values["decimallatitude"])
                        if not math.isfinite(lat):
                            raise ValueError
                    except ValueError:
                        counts["invalid_latitude"] += 1
                        lat = None

                lon = None
                if not values["decimallongitude"]:
                    counts["missing_longitude"] += 1
                else:
                    try:
                        lon = float(values["decimallongitude"])
                        if not math.isfinite(lon):
                            raise ValueError
                    except ValueError:
                        counts["invalid_longitude"] += 1
                        lon = None

                if not values["locality"]:
                    counts["missing_locality"] += 1
                if not values["samplingprotocol"]:
                    counts["missing_samplingprotocol"] += 1

                complete = (
                    bool(values["eventid"])
                    and interval is not None
                    and lat is not None
                    and lon is not None
                    and bool(values["locality"])
                )
                if not complete:
                    continue

                counts["complete_case_rows"] += 1
                coord = (lat, lon)
                coordinates.add(coord)
                months = _months(*interval)
                all_months.update(months)
                bucket = locality[values["locality"]]
                bucket["rows"] += 1
                bucket["coordinates"].add(coord)
                bucket["months"].update(months)

    locality_summaries = sorted(
        (
            {
                "complete_case_rows": value["rows"],
                "unique_coordinate_pairs": len(value["coordinates"]),
                "distinct_calendar_month_count": len(value["months"]),
            }
            for value in locality.values()
        ),
        key=lambda x: (
            x["complete_case_rows"],
            x["unique_coordinate_pairs"],
            x["distinct_calendar_month_count"],
        ),
    )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-deployment-completeness-result-v1",
        "status": "E5_RESPONSE_BLIND_QLD_DEPLOYMENT_COMPLETENESS",
        "source": {
            "archive_sha256": archive_sha,
            "verbatim_event_file": contract["source"]["verbatim_event_file"],
        },
        "complete_case_rule": contract["complete_case_rule"],
        "missingness": counts,
        "complete_case_geometry": {
            "unique_coordinate_pairs": len(coordinates),
            "unique_localities": len(locality),
            "distinct_calendar_months": sorted(all_months),
            "distinct_calendar_month_count": len(all_months),
            "anonymized_locality_summaries": locality_summaries,
        },
        "capacity_hints": {
            "G2_COMPLETE_CASE_METADATA": (
                "AVAILABLE_WITH_EXCLUSIONS"
                if counts["complete_case_rows"] > 0 and counts["complete_case_rows"] < counts["deployment_rows"]
                else "COMPLETE"
                if counts["complete_case_rows"] == counts["deployment_rows"]
                else "UNAVAILABLE"
            ),
            "G5_GLOBAL_PHYSICAL_CAPACITY": len(coordinates) >= 30,
            "G6_GLOBAL_SIX_MONTH_CAPACITY": len(all_months) >= 6,
        },
        "response_boundary": {
            "verbatim_event_prefix_rows_scanned": True,
            "eventremarks_values_decoded": 0,
            "event_core_rows_read": 0,
            "emof_rows_read": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
            "species_or_taxon_values_read": 0,
            "raw_eventids_reported": 0,
            "raw_eventdates_reported": 0,
            "raw_coordinates_reported": 0,
            "raw_localities_reported": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_child_contract_required_before_camera_metadata_join_or_split": True,
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
