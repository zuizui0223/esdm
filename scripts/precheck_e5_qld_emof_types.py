#!/usr/bin/env python3
"""Response-blind measurement-type precheck for Queensland ALA eMoF extension."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-ala-emof-measurement-type-response-blind-v1"


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(value: str | None) -> str:
    if not value:
        return ""
    return re.split(r"[/#]", str(value).strip())[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {r"\t":"\t", r"\n":"\n", r"\r":"\r", r"\r\n":"\r\n"}.get(value, value)


def _first_child(element: ET.Element, name: str):
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def _children(element: ET.Element, name: str):
    return [child for child in element if _local(child.tag) == name]


def _file_location(section: ET.Element) -> str:
    files = _first_child(section, "files")
    if files is None:
        raise ValueError("DwC section missing files")
    loc = _first_child(files, "location")
    if loc is None or not (loc.text or "").strip():
        raise ValueError("DwC section missing file location")
    return str(loc.text).strip()


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


def _classify(name: str, contract: dict) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    patterns = contract["target_type_patterns"]
    if any(token in normalized for token in patterns["response_like_types"]):
        return "RESPONSE_LIKE_TYPE_VALUE_REMAINS_FORBIDDEN"
    if any(token in normalized for token in patterns["detection_metadata"]):
        return "POTENTIAL_DETECTION_METADATA"
    if any(token in normalized for token in patterns["source_protocol_metadata"]):
        return "POTENTIAL_SOURCE_PROTOCOL_METADATA"
    return "UNCLASSIFIED"


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland eMoF contract")

    firewall = contract["response_firewall"]
    for key in (
        "measurement_value_values_may_be_retained",
        "measurement_value_values_may_be_reported",
        "measurement_determined_by_values_may_be_retained",
        "measurement_determined_date_values_may_be_retained",
        "event_core_rows_read_authorized",
        "verbatim_event_rows_read_authorized",
        "occurrence_extension_data_read_authorized",
        "verbatim_occurrence_rows_read_authorized",
        "multimedia_rows_read_authorized",
        "species_or_taxon_value_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    raw = archive_path.read_bytes()
    observed_sha = hashlib.sha256(raw).hexdigest()
    if observed_sha != contract["source"]["archive_sha256"]:
        raise ValueError("archive SHA256 drift")

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        root = ET.fromstring(archive.read(contract["source"]["meta_xml_member"]))
        matches = []
        for ext in _children(root, "extension"):
            spec = _section(ext)
            if (
                spec["file"] == contract["source"]["extension_file"]
                and spec["row_type"] == contract["source"]["extension_row_type"]
            ):
                matches.append(spec)
        if len(matches) != 1:
            raise ValueError("expected exactly one pinned eMoF extension")
        spec = matches[0]

        declared = sorted(set(spec["fields"].values()))
        if declared != sorted(contract["expected_declared_terms"]):
            raise ValueError(f"eMoF schema drift: {declared!r}")

        authorized = set(contract["fields_authorized_for_values"])
        forbidden = set(contract["fields_declared_but_value_retention_reporting_forbidden"])
        if authorized & forbidden:
            raise ValueError("authorized and forbidden fields overlap")

        index_by_term = {
            term: idx
            for idx, term in spec["fields"].items()
            if term in authorized
        }
        member = str(spec["file"])
        if member not in archive.namelist():
            raise ValueError("pinned eMoF file missing")
        text = archive.read(member).decode(str(spec["encoding"] or "UTF-8"), errors="strict")

    handle = io.StringIO(text)
    for _ in range(int(spec["ignore_header_lines"])):
        next(handle, None)
    reader = csv.reader(
        handle,
        delimiter=str(spec["delimiter"]),
        quotechar=str(spec["quotechar"] or '"'),
    )

    max_index = max(
        list(spec["fields"])
        + ([int(spec["coreid_index"])] if spec["coreid_index"] is not None else [])
    )

    row_count = 0
    invalid_width = 0
    event_ids = set()
    type_counts = collections.Counter()
    type_id_counts = collections.Counter()

    def get(cells, term):
        idx = index_by_term.get(term)
        return str(cells[idx]).strip() if idx is not None else ""

    for cells in reader:
        if not cells or not any(str(v).strip() for v in cells):
            continue
        if len(cells) <= max_index:
            invalid_width += 1
            continue
        row_count += 1

        event_id = get(cells, "eventid")
        measurement_type = get(cells, "measurementtype")
        measurement_type_id = get(cells, "measurementtypeid")

        if event_id:
            event_ids.add(event_id)
        if measurement_type:
            type_counts[measurement_type] += 1
        if measurement_type_id:
            type_id_counts[measurement_type_id] += 1

        # Deliberately never index/read measurementValue or determined-by/date cells.

    type_records = []
    for name, count in sorted(type_counts.items()):
        type_records.append({
            "measurement_type": name,
            "row_count": int(count),
            "classification": _classify(name, contract),
        })

    classes = collections.Counter(r["classification"] for r in type_records)

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-ala-emof-measurement-type-precheck-v1",
        "status": "E5_RESPONSE_BLIND_QLD_EMOF_TYPE_PRECHECK",
        "source": {
            "archive_url": contract["source"]["archive_url"],
            "archive_sha256": observed_sha,
            "extension_file": member,
            "extension_row_type": spec["row_type"],
            "declared_terms": declared,
        },
        "geometry": {
            "row_count": row_count,
            "invalid_width_rows": invalid_width,
            "unique_linked_event_ids": len(event_ids),
            "distinct_measurement_type_count": len(type_counts),
            "distinct_measurement_type_id_count": len(type_id_counts),
        },
        "measurement_types": type_records,
        "classification_counts": dict(sorted(classes.items())),
        "measurement_type_ids": {
            "distinct_nonempty_count": len(type_id_counts),
            "values": dict(sorted(type_id_counts.items()))
            if len(type_id_counts) <= 50 else {},
            "value_hashes": (
                sorted(hashlib.sha256(v.encode("utf-8")).hexdigest() for v in type_id_counts)
                if len(type_id_counts) > 50 else []
            ),
        },
        "capacity_hints": {
            "G3_source_protocol_metadata_type_present": any(
                r["classification"] == "POTENTIAL_SOURCE_PROTOCOL_METADATA"
                for r in type_records
            ),
            "G4_detection_metadata_type_present": any(
                r["classification"] == "POTENTIAL_DETECTION_METADATA"
                for r in type_records
            ),
        },
        "response_boundary": {
            "event_core_rows_read": 0,
            "verbatim_event_rows_read": 0,
            "emof_rows_read": row_count,
            "measurement_values_read": 0,
            "measurement_values_retained": 0,
            "measurement_values_reported": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
            "species_or_taxon_values_read": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_child_contract_required_before_any_measurement_value": True,
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
