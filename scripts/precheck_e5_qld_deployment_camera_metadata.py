#!/usr/bin/env python3
"""Response-blind deployment/camera metadata qualification for E5 Queensland."""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-deployment-camera-metadata-qualification-v1"


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(term: str | None) -> str:
    if not term:
        return ""
    raw = str(term).strip().replace("#", "/")
    return raw.rsplit("/", 1)[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {r"\t": "\t", r"\n": "\n", r"\r": "\r", r"\r\n": "\r\n"}.get(value, value)


def _first_child(element: ET.Element, name: str) -> ET.Element | None:
    return next((c for c in element if _local(c.tag) == name), None)


def _section(section: ET.Element) -> dict[str, object]:
    files = _first_child(section, "files")
    if files is None:
        raise ValueError("section missing files")
    loc = _first_child(files, "location")
    if loc is None or not (loc.text or "").strip():
        raise ValueError("section missing location")
    fields = {}
    for child in section:
        if _local(child.tag) == "field" and "index" in child.attrib:
            fields[int(child.attrib["index"])] = _term_tail(child.attrib.get("term"))
    coreid = _first_child(section, "coreid")
    return {
        "row_type": str(section.attrib.get("rowType", "")),
        "file": str(loc.text).strip(),
        "encoding": str(section.attrib.get("encoding", "UTF-8")),
        "delimiter": _decode_sep(section.attrib.get("fieldsTerminatedBy"), "\t"),
        "quotechar": _decode_sep(section.attrib.get("fieldsEnclosedBy"), '"'),
        "ignore_header_lines": int(section.attrib.get("ignoreHeaderLines", "0") or 0),
        "fields": fields,
        "coreid_index": (
            int(coreid.attrib["index"])
            if coreid is not None and "index" in coreid.attrib
            else None
        ),
    }


def _find_section(root: ET.Element, filename: str) -> dict[str, object]:
    matches = []
    for child in root:
        if _local(child.tag) not in {"core", "extension"}:
            continue
        spec = _section(child)
        if spec["file"] == filename:
            matches.append(spec)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one section for {filename!r}, got {len(matches)}")
    return matches[0]


def _term_index(spec: dict[str, object], term: str) -> int:
    matches = [i for i, name in dict(spec["fields"]).items() if name == term]
    if len(matches) != 1:
        raise ValueError(f"expected one {term} index, got {matches}")
    return matches[0]


def _parse_date(value: str) -> date:
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return date.fromisoformat(raw[:10])


def _interval(value: str) -> tuple[date, date]:
    raw = str(value).strip()
    if not raw:
        raise ValueError("empty eventDate")
    parts = raw.split("/", 1)
    start = _parse_date(parts[0])
    end = _parse_date(parts[1]) if len(parts) == 2 else start
    if end < start:
        raise ValueError("event interval ends before start")
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


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _classify_remarks(text: str, contract: dict) -> str:
    normalized = " ".join(str(text).lower().replace("_", " ").replace("-", " ").split())
    rules = contract["deployment_classification"]
    road = any(token.replace("-", " ") in normalized for token in rules["road_tokens"])
    bush = any(token.replace("-", " ") in normalized for token in rules["bush_tokens"])
    if road and not bush:
        return "ROAD_TRAIL"
    if bush and not road:
        return "BUSH"
    if road and bush:
        return "AMBIGUOUS"
    return "UNKNOWN"


def _read_verbatim_deployments(z: zipfile.ZipFile, spec: dict[str, object], contract: dict):
    encoding = str(spec["encoding"] or "UTF-8")
    delimiter = str(spec["delimiter"])
    quotechar = str(spec["quotechar"] or '"')
    with z.open(str(spec["file"]), "r") as raw:
        text = io.TextIOWrapper(raw, encoding=encoding, errors="strict", newline="")
        for _ in range(int(spec["ignore_header_lines"])):
            next(text, None)
        reader = csv.reader(text, delimiter=delimiter, quotechar=quotechar)
        fields = dict(spec["fields"])
        max_index = max(fields)
        rows = []
        for cells in reader:
            if not cells or not any(str(x).strip() for x in cells):
                continue
            if len(cells) <= max_index:
                raise ValueError("short VerbatimEvent row")
            row = {term: str(cells[i]).strip() for i, term in fields.items()}
            if row.get("eventtype", "").casefold() != "deployment":
                continue
            event_id = row.get("eventid", "")
            if not event_id:
                raise ValueError("Deployment row missing eventID")
            lat = float(row["decimallatitude"])
            lon = float(row["decimallongitude"])
            start, end = _interval(row["eventdate"])
            rows.append({
                "event_id": event_id,
                "parent_event_id": row.get("parenteventid", ""),
                "deployment_groups": row.get("deploymentgroups", ""),
                "locality": row.get("locality", ""),
                "lat": lat,
                "lon": lon,
                "start": start,
                "end": end,
                "months": _months(start, end),
                "placement_class": _classify_remarks(row.get("eventremarks", ""), contract),
                "sampling_protocol": row.get("samplingprotocol", ""),
                "habitat": row.get("habitat", ""),
            })
    return rows


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


def _read_emof_allowlist(z: zipfile.ZipFile, spec: dict[str, object], contract: dict):
    allow = set(contract["emof_value_allowlist"])
    type_index = _term_index(spec, "measurementtype")
    value_index = _term_index(spec, "measurementvalue")
    core_index = int(spec["coreid_index"]) if spec["coreid_index"] is not None else _term_index(spec, "eventid")
    encoding = str(spec["encoding"] or "UTF-8")
    delimiter = str(spec["delimiter"]).encode()
    quote = str(spec["quotechar"] or '"').encode()
    if len(delimiter) != 1 or len(quote) != 1:
        raise ValueError("only single-byte delimiter/quote supported")

    by_core = defaultdict(lambda: defaultdict(list))
    total_rows = 0
    allowed_rows = 0
    nonallowed_value_decodes = 0
    with z.open(str(spec["file"]), "r") as raw:
        for _ in range(int(spec["ignore_header_lines"])):
            raw.readline()
        for raw_line in raw:
            if not raw_line.strip():
                continue
            total_rows += 1
            prefix = _prefix_field_bytes(raw_line, delimiter, quote, max(core_index, type_index))
            if len(prefix) <= max(core_index, type_index):
                raise ValueError("cannot parse EMoF prefix")
            core = prefix[core_index].strip().strip(quote).decode(encoding, errors="strict")
            mtype = prefix[type_index].strip().strip(quote).decode(encoding, errors="strict")
            if mtype not in allow:
                continue
            allowed_rows += 1
            # Full-row decoding occurs only after the measurementType has matched the
            # pre-frozen response-independent allowlist.
            row_text = raw_line.decode(encoding, errors="strict")
            cells = next(csv.reader([row_text], delimiter=delimiter.decode(), quotechar=quote.decode()))
            if len(cells) <= value_index:
                raise ValueError("allowlisted EMoF row lacks measurementValue")
            by_core[core][mtype].append(str(cells[value_index]).strip())

    return by_core, {
        "total_rows": total_rows,
        "allowlisted_rows": allowed_rows,
        "nonallowlisted_measurementvalue_values_decoded": nonallowed_value_decodes,
    }


def _overlap(a, b) -> bool:
    return max(a["start"], b["start"]) <= min(a["end"], b["end"])


def _pair_diagnostic(rows, contract):
    low = float(contract["pairing_diagnostic"]["distance_m_min"])
    high = float(contract["pairing_diagnostic"]["distance_m_max"])
    candidates = []
    for i, a in enumerate(rows):
        if a["placement_class"] not in {"ROAD_TRAIL", "BUSH"}:
            continue
        for j in range(i + 1, len(rows)):
            b = rows[j]
            if b["placement_class"] not in {"ROAD_TRAIL", "BUSH"}:
                continue
            if a["placement_class"] == b["placement_class"]:
                continue
            if a["locality"] != b["locality"] or not _overlap(a, b):
                continue
            d = _haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])
            if low <= d <= high:
                candidates.append((d, i, j, a["locality"]))
    candidates.sort()
    used = set()
    pairs = []
    for d, i, j, locality in candidates:
        if i in used or j in used:
            continue
        used.add(i)
        used.add(j)
        pairs.append((d, locality))
    return pairs


def _nearest_neighbor_distances(rows):
    by_locality = defaultdict(set)
    for r in rows:
        by_locality[r["locality"]].add((r["lat"], r["lon"]))
    values = []
    for coords in by_locality.values():
        coords = list(coords)
        if len(coords) < 2:
            continue
        for i, a in enumerate(coords):
            ds = [
                _haversine_m(a[0], a[1], b[0], b[1])
                for j, b in enumerate(coords)
                if j != i
            ]
            if ds:
                values.append(min(ds))
    return values


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland deployment-camera contract")

    raw = archive_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != contract["source"]["archive_sha256"]:
        raise ValueError("archive SHA256 drift")

    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        root = ET.fromstring(z.read(contract["source"]["meta_xml_member"]))
        verbatim = _find_section(root, contract["source"]["verbatim_event_file"])
        emof = _find_section(root, contract["source"]["emof_file"])

        forbidden_verbatim_terms = {
            "scientificname", "taxonkey", "taxonid", "occurrenceid",
            "individualcount", "occurrencestatus", "species",
        }
        declared_verbatim_terms = set(verbatim["fields"].values())
        overlap = sorted(declared_verbatim_terms & forbidden_verbatim_terms)
        if overlap:
            raise ValueError(
                f"VerbatimEvent unexpectedly declares biological response terms: {overlap}"
            )

        deployments = _read_verbatim_deployments(z, verbatim, contract)
        emof_by_core, emof_scan = _read_emof_allowlist(z, emof, contract)

    event_ids = {r["event_id"] for r in deployments}
    matched = {k: v for k, v in emof_by_core.items() if k in event_ids}
    unmatched_emof_core_count = len(set(emof_by_core) - event_ids)

    for r in deployments:
        r["camera"] = matched.get(r["event_id"], {})

    allow = list(contract["emof_value_allowlist"])
    completeness = {}
    for name in allow:
        exactly_one = sum(len(r["camera"].get(name, [])) == 1 for r in deployments)
        missing = sum(len(r["camera"].get(name, [])) == 0 for r in deployments)
        duplicates = sum(len(r["camera"].get(name, [])) > 1 for r in deployments)
        completeness[name] = {
            "exactly_one": exactly_one,
            "missing": missing,
            "duplicate_value_rows": duplicates,
        }

    camera_ids = {
        values[0]
        for r in deployments
        if len((values := r["camera"].get("cameraID", []))) == 1 and values[0]
    }

    def value_counts(name):
        c = Counter()
        for r in deployments:
            for value in r["camera"].get(name, []):
                if value:
                    c[value] += 1
        return dict(sorted(c.items()))

    localities = {}
    for locality in sorted({r["locality"] for r in deployments}):
        rr = [r for r in deployments if r["locality"] == locality]
        months = sorted(set().union(*(r["months"] for r in rr)))
        localities[locality] = {
            "deployment_rows": len(rr),
            "unique_coordinate_pairs": len({(r["lat"], r["lon"]) for r in rr}),
            "distinct_calendar_months": months,
            "distinct_calendar_month_count": len(months),
            "placement_class_counts": dict(sorted(Counter(r["placement_class"] for r in rr).items())),
            "camera_model_counts": dict(sorted(Counter(
                v
                for r in rr
                for v in r["camera"].get("cameraModel", [])
                if v
            ).items())),
        }

    pairs = _pair_diagnostic(deployments, contract)
    nearest = _nearest_neighbor_distances(deployments)
    pair_distances = [d for d, _ in pairs]

    result = {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-deployment-camera-metadata-qualification-result-v1",
        "status": "E5_RESPONSE_BLIND_QLD_DEPLOYMENT_CAMERA_METADATA_PRECHECK",
        "source": {
            "archive_sha256": sha,
            "verbatim_event_file": contract["source"]["verbatim_event_file"],
            "emof_file": contract["source"]["emof_file"],
        },
        "geometry": {
            "deployment_rows": len(deployments),
            "unique_coordinate_pairs": len({(r["lat"], r["lon"]) for r in deployments}),
            "unique_localities": len(localities),
            "global_distinct_calendar_months": sorted(set().union(*(r["months"] for r in deployments))),
            "localities": localities,
        },
        "camera_metadata": {
            "emof_scan": emof_scan,
            "matched_emof_core_count": len(matched),
            "unmatched_emof_core_count": unmatched_emof_core_count,
            "distinct_camera_id_count": len(camera_ids),
            "raw_camera_ids_reported": 0,
            "completeness": completeness,
            "camera_model_counts": value_counts("cameraModel"),
            "camera_delay_counts": value_counts("cameraDelay"),
            "camera_height_counts": value_counts("cameraHeight"),
            "camera_tilt_counts": value_counts("cameraTilt"),
        },
        "placement_and_pairing": {
            "placement_class_counts": dict(sorted(Counter(r["placement_class"] for r in deployments).items())),
            "matched_road_bush_pair_count": len(pairs),
            "matched_pair_locality_count": len({loc for _, loc in pairs}),
            "matched_pair_distance_m": {
                "minimum": min(pair_distances) if pair_distances else None,
                "median": statistics.median(pair_distances) if pair_distances else None,
                "maximum": max(pair_distances) if pair_distances else None,
            },
            "nearest_neighbor_distance_m": {
                "count": len(nearest),
                "minimum": min(nearest) if nearest else None,
                "median": statistics.median(nearest) if nearest else None,
                "maximum": max(nearest) if nearest else None,
                "fraction_25_to_100m": (
                    sum(25 <= x <= 100 for x in nearest) / len(nearest)
                    if nearest else None
                ),
            },
        },
        "gate_hints": {
            "G2_SCHEMA_EFFORT_TIME": (
                "PASS_METADATA_COMPONENT"
                if len(deployments) == 271 and all(v["missing"] == 0 for v in completeness.values())
                else "PARTIAL"
            ),
            "G3_CROSSED_DOMAIN": "DESIGN_POTENTIAL_ONLY",
            "G4_DETECTION_IDENTIFIABILITY": "DESIGN_POTENTIAL_ONLY",
            "G5_PHYSICAL_REPLICATION": "CAPACITY_ONLY",
            "G6_TEMPORAL_SUPPORT": "CAPACITY_ONLY",
        },
        "response_boundary": {
            "event_core_rows_read": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
            "species_or_taxon_values_read": 0,
            "trigger_biological_outcomes_interpreted": False,
            "raw_eventremarks_reported": 0,
            "raw_camera_ids_reported": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "split_and_model_freeze_child_required": True,
        },
    }
    return result


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
