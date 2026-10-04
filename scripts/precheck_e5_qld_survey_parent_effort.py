#!/usr/bin/env python3
"""Response-blind Survey->Deployment effort inheritance diagnostic for Queensland E5."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-survey-parent-effort-response-blind-v1"


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
    values = [i for i, name in dict(spec["fields"]).items() if name == term]
    if len(values) != 1:
        raise ValueError(f"expected one {term} index, got {values}")
    return values[0]


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
    parts = raw.split("/", 1)
    start = _parse_date(parts[0])
    end = _parse_date(parts[1]) if len(parts) == 2 else start
    if end < start:
        raise ValueError("reversed")
    return start, end


def _months(start: date, end: date) -> set[str]:
    y, m = start.year, start.month
    out = set()
    while (y, m) <= (end.year, end.month):
        out.add(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland Survey-parent contract")

    rule = contract["inheritance_rule"]
    if rule.get("trigger_eventdate_use_authorized") is not False:
        raise ValueError("Trigger eventDate must remain forbidden")
    if rule.get("biological_response_use_authorized") is not False:
        raise ValueError("biological response must remain forbidden")

    fw = contract["response_firewall"]
    for key in (
        "trigger_eventdate_decode_authorized",
        "eventremarks_value_decode_authorized",
        "raw_eventid_report_authorized",
        "raw_parenteventid_report_authorized",
        "raw_eventdate_report_authorized",
        "raw_coordinates_report_authorized",
        "raw_locality_report_authorized",
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
        terms = (
            "eventid", "parenteventid", "eventdate", "eventtype",
            "deploymentgroups", "decimallatitude", "decimallongitude", "locality",
        )
        idx = {term: _index(spec, term) for term in terms}
        max_index = max(idx.values())
        delimiter = str(spec["delimiter"]).encode()
        quote = str(spec["quotechar"] or '"').encode()
        if len(delimiter) != 1 or len(quote) != 1:
            raise ValueError("only single-byte delimiter/quote supported")
        encoding = str(spec["encoding"] or "UTF-8")

        surveys: dict[str, list[dict[str, object]]] = {}
        deployments = []
        counts = {
            "survey_rows": 0,
            "survey_missing_eventid": 0,
            "survey_missing_eventdate": 0,
            "survey_invalid_eventdate": 0,
            "deployment_rows": 0,
            "deployment_missing_eventid": 0,
            "deployment_missing_parent_eventid": 0,
            "deployment_missing_coordinates": 0,
            "deployment_missing_locality": 0,
        }
        trigger_rows_skipped = 0

        with z.open(str(spec["file"]), "r") as stream:
            for _ in range(int(spec["ignore_header_lines"])):
                stream.readline()
            for raw_line in stream:
                if not raw_line.strip():
                    continue
                prefix = _prefix_field_bytes(raw_line, delimiter, quote, max_index)
                if len(prefix) <= max_index:
                    raise ValueError("cannot parse VerbatimEvent prefix")

                event_type = _decode_field(prefix[idx["eventtype"]], encoding, quote)
                folded = event_type.casefold()

                if folded == "trigger":
                    trigger_rows_skipped += 1
                    continue

                if folded == "survey":
                    counts["survey_rows"] += 1
                    event_id = _decode_field(prefix[idx["eventid"]], encoding, quote)
                    if not event_id:
                        counts["survey_missing_eventid"] += 1
                    event_date = _decode_field(prefix[idx["eventdate"]], encoding, quote)
                    interval = None
                    if not event_date:
                        counts["survey_missing_eventdate"] += 1
                    else:
                        try:
                            interval = _interval(event_date)
                        except ValueError:
                            counts["survey_invalid_eventdate"] += 1
                    if event_id:
                        surveys.setdefault(event_id, []).append({
                            "interval": interval,
                            "deployment_group": _decode_field(
                                prefix[idx["deploymentgroups"]], encoding, quote
                            ),
                        })
                    continue

                if folded != "deployment":
                    continue

                counts["deployment_rows"] += 1
                event_id = _decode_field(prefix[idx["eventid"]], encoding, quote)
                parent_id = _decode_field(prefix[idx["parenteventid"]], encoding, quote)
                if not event_id:
                    counts["deployment_missing_eventid"] += 1
                if not parent_id:
                    counts["deployment_missing_parent_eventid"] += 1

                lat_raw = _decode_field(prefix[idx["decimallatitude"]], encoding, quote)
                lon_raw = _decode_field(prefix[idx["decimallongitude"]], encoding, quote)
                lat = lon = None
                try:
                    lat = float(lat_raw)
                    lon = float(lon_raw)
                    if not math.isfinite(lat) or not math.isfinite(lon):
                        lat = lon = None
                except ValueError:
                    lat = lon = None
                if lat is None or lon is None:
                    counts["deployment_missing_coordinates"] += 1

                locality = _decode_field(prefix[idx["locality"]], encoding, quote)
                if not locality:
                    counts["deployment_missing_locality"] += 1

                deployments.append({
                    "event_id_present": bool(event_id),
                    "parent_id": parent_id,
                    "coordinate": (lat, lon) if lat is not None and lon is not None else None,
                    "locality": locality,
                    "deployment_group": _decode_field(
                        prefix[idx["deploymentgroups"]], encoding, quote
                    ),
                })

    unique_parent_matches = 0
    valid_interval_matches = 0
    duplicate_parent_matches = 0
    missing_parent_matches = 0
    group_matches = 0
    group_mismatches = 0
    inherited_months = set()
    inherited_coordinates = set()
    inherited_localities = set()
    parent_counts = Counter()

    for row in deployments:
        parent_id = row["parent_id"]
        matches = surveys.get(parent_id, []) if parent_id else []
        if len(matches) == 0:
            missing_parent_matches += 1
            continue
        if len(matches) > 1:
            duplicate_parent_matches += 1
            continue

        unique_parent_matches += 1
        survey = matches[0]
        if row["deployment_group"] and survey["deployment_group"]:
            if row["deployment_group"] == survey["deployment_group"]:
                group_matches += 1
            else:
                group_mismatches += 1

        interval = survey["interval"]
        if interval is None:
            continue
        valid_interval_matches += 1
        parent_counts[parent_id] += 1
        inherited_months.update(_months(*interval))
        if row["coordinate"] is not None:
            inherited_coordinates.add(row["coordinate"])
        if row["locality"]:
            inherited_localities.add(row["locality"])

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-survey-parent-effort-result-v1",
        "status": "E5_RESPONSE_BLIND_QLD_SURVEY_PARENT_EFFORT",
        "source": {
            "archive_sha256": archive_sha,
            "verbatim_event_file": contract["source"]["verbatim_event_file"],
        },
        "inheritance_rule": rule,
        "geometry": {
            **counts,
            "unique_parent_survey_matches": unique_parent_matches,
            "duplicate_parent_survey_matches": duplicate_parent_matches,
            "missing_parent_survey_matches": missing_parent_matches,
            "deployments_with_valid_inherited_interval": valid_interval_matches,
            "deployment_group_matches": group_matches,
            "deployment_group_mismatches": group_mismatches,
            "derived_unique_coordinate_pairs": len(inherited_coordinates),
            "derived_unique_localities": len(inherited_localities),
            "derived_distinct_calendar_months": sorted(inherited_months),
            "derived_distinct_calendar_month_count": len(inherited_months),
            "anonymized_parent_survey_deployment_counts": sorted(parent_counts.values()),
        },
        "capacity_hints": {
            "G2_PARENT_INTERVAL_METADATA": (
                "COMPLETE"
                if valid_interval_matches == counts["deployment_rows"] and counts["deployment_rows"] > 0
                else "PARTIAL"
                if valid_interval_matches > 0
                else "UNAVAILABLE"
            ),
            "G5_GLOBAL_PHYSICAL_CAPACITY": len(inherited_coordinates) >= 30,
            "G6_GLOBAL_SIX_MONTH_CAPACITY": len(inherited_months) >= 6,
        },
        "response_boundary": {
            "trigger_rows_skipped_without_eventdate_decode": trigger_rows_skipped,
            "trigger_eventdates_decoded": 0,
            "eventremarks_values_decoded": 0,
            "event_core_rows_read": 0,
            "emof_rows_read": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
            "species_or_taxon_values_read": 0,
            "raw_eventids_reported": 0,
            "raw_parent_eventids_reported": 0,
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
