#!/usr/bin/env python3
"""Response-blind measurementType-only precheck for Queensland ALA EMoF."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET


EXPECTED_CONTRACT_ID = "e5-qld-ala-emof-measurementtype-response-blind-v1"


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _term_tail(term: str | None) -> str:
    if not term:
        return ""
    return re.split(r"[/#]", str(term).strip())[-1].lower()


def _decode_sep(value: str | None, default: str) -> str:
    if value is None or value == "":
        return default
    return {r"\t": "\t", r"\n": "\n", r"\r": "\r", r"\r\n": "\r\n"}.get(value, value)


def _first_child(element: ET.Element, name: str) -> ET.Element | None:
    return next((c for c in element if _local(c.tag) == name), None)


def _section(section: ET.Element) -> dict[str, object]:
    files = _first_child(section, "files")
    if files is None:
        raise ValueError("extension missing files")
    loc = _first_child(files, "location")
    if loc is None or not (loc.text or "").strip():
        raise ValueError("extension missing file location")

    fields = {}
    for child in section:
        if _local(child.tag) != "field" or "index" not in child.attrib:
            continue
        fields[int(child.attrib["index"])] = _term_tail(child.attrib.get("term"))

    coreid = _first_child(section, "coreid")
    coreid_index = (
        int(coreid.attrib["index"])
        if coreid is not None and "index" in coreid.attrib
        else None
    )
    return {
        "row_type": str(section.attrib.get("rowType", "")),
        "file": str(loc.text).strip(),
        "encoding": str(section.attrib.get("encoding", "UTF-8")),
        "delimiter": _decode_sep(section.attrib.get("fieldsTerminatedBy"), "\t"),
        "quotechar": _decode_sep(section.attrib.get("fieldsEnclosedBy"), '"'),
        "ignore_header_lines": int(section.attrib.get("ignoreHeaderLines", "0") or 0),
        "fields": fields,
        "coreid_index": coreid_index,
    }


def _classify(name: str, contract: dict) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", str(name).lower())
    response = tuple(
        re.sub(r"[^a-z0-9]+", "", str(x).lower())
        for x in contract["measurementtype_policy"]["response_bearing_patterns"]
    )
    independent = tuple(
        re.sub(r"[^a-z0-9]+", "", str(x).lower())
        for x in contract["measurementtype_policy"]["response_independent_patterns"]
    )
    if any(token and token in normalized for token in response):
        return "MASKED_POTENTIALLY_RESPONSE_BEARING"
    if any(token and token in normalized for token in independent):
        return "POTENTIALLY_RESPONSE_INDEPENDENT"
    return "UNCLASSIFIED"


def precheck(archive_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Queensland EMoF contract")

    fw = contract["response_firewall"]
    for key in (
        "measurementtypeid_read_authorized",
        "measurementvalue_decode_authorized",
        "measurementvalue_retain_authorized",
        "measurementvalue_report_authorized",
        "measurementdeterminedby_values_authorized",
        "measurementdetermineddate_values_authorized",
        "measurementid_values_authorized",
        "event_core_rows_read_authorized",
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
        meta_name = contract["source"]["meta_xml_member"]
        root = ET.fromstring(z.read(meta_name))
        matches = []
        for child in root:
            if _local(child.tag) != "extension":
                continue
            spec = _section(child)
            if (
                spec["file"] == contract["source"]["extension_file"]
                and spec["row_type"] == contract["source"]["extension_row_type"]
            ):
                matches.append(spec)
        if len(matches) != 1:
            raise ValueError(f"expected one pinned EMoF extension, got {len(matches)}")
        spec = matches[0]

        type_index = next(
            (i for i, term in spec["fields"].items() if term == "measurementtype"),
            None,
        )
        value_index = next(
            (i for i, term in spec["fields"].items() if term == "measurementvalue"),
            None,
        )
        if type_index is None or value_index is None:
            raise ValueError("measurementType/measurementValue schema missing")
        if value_index <= type_index:
            raise ValueError("measurementValue precedes measurementType; cannot blind safely")

        delimiter = str(spec["delimiter"])
        quotechar = str(spec["quotechar"] or '"')
        if len(delimiter.encode()) != 1 or len(quotechar.encode()) != 1:
            raise ValueError("only single-byte delimiter/quote supported")
        delim_b = delimiter.encode()
        quote_b = quotechar.encode()

        member = str(spec["file"])
        stream = z.open(member, "r")
        for _ in range(int(spec["ignore_header_lines"])):
            stream.readline()

        type_counts: Counter[str] = Counter()
        masked_response_type_rows = 0
        row_count = 0
        prefix_parse_failures = 0
        measurementvalue_values_decoded = 0
        measurementvalue_values_retained = 0
        measurementvalue_values_reported = 0

        for raw_line in stream:
            if not raw_line.strip():
                continue
            row_count += 1

            # Split only through measurementType. The remaining bytes (which include
            # measurementValue) are deliberately left undecoded and immediately dropped.
            pieces = raw_line.split(delim_b, type_index + 1)
            if len(pieces) <= type_index:
                prefix_parse_failures += 1
                continue
            prefix = pieces[: type_index + 1]
            # Fail closed rather than attempting quoted CSV semantics that could force
            # decoding later fields.
            if any(quote_b in field for field in prefix):
                prefix_parse_failures += 1
                continue

            try:
                mtype = prefix[type_index].decode(
                    str(spec["encoding"] or "UTF-8"), errors="strict"
                ).strip()
            except UnicodeDecodeError:
                prefix_parse_failures += 1
                continue
            if not mtype:
                continue

            cls = _classify(mtype, contract)
            if cls == "MASKED_POTENTIALLY_RESPONSE_BEARING":
                masked_response_type_rows += 1
            else:
                type_counts[mtype] += 1

    safe_types = []
    for name, count in sorted(type_counts.items()):
        safe_types.append({
            "measurement_type": name,
            "row_count": int(count),
            "schema_classification": _classify(name, contract),
        })

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-emof-measurementtype-precheck-v1",
        "status": "E5_RESPONSE_BLIND_QLD_EMOF_MEASUREMENTTYPE_PRECHECK",
        "source": {
            "archive_sha256": archive_sha,
            "extension_file": contract["source"]["extension_file"],
            "extension_row_type": contract["source"]["extension_row_type"],
            "declared_terms": sorted(set(spec["fields"].values())),
            "measurementtype_index": int(type_index),
            "measurementvalue_index": int(value_index),
        },
        "measurement_types": {
            "safe_or_unclassified_distinct_count": len(safe_types),
            "safe_or_unclassified": safe_types,
            "masked_potentially_response_bearing_rows": masked_response_type_rows,
        },
        "scan": {
            "row_count": row_count,
            "prefix_parse_failures": prefix_parse_failures,
            "measurementvalue_values_decoded": measurementvalue_values_decoded,
            "measurementvalue_values_retained": measurementvalue_values_retained,
            "measurementvalue_values_reported": measurementvalue_values_reported,
        },
        "response_boundary": {
            "event_core_rows_read": 0,
            "occurrence_rows_read": 0,
            "verbatim_occurrence_rows_read": 0,
            "multimedia_rows_read": 0,
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
            "separate_value_allowlist_child_contract_required": True,
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
