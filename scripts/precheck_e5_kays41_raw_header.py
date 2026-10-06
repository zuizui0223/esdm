#!/usr/bin/env python3
"""One-shot response-blind header precheck for Kays41 Spatial_Raw_detections.csv."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


EXPECTED_CONTRACT_ID = "e5-kays41-spatial-raw-header-response-blind-v1"


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.casefold())


def _match_concepts(header: list[str]) -> dict[str, list[str]]:
    patterns = {
        "deployment_identifier": (
            r"deploymentid", r"deploymentidentifier", r"deployment"
        ),
        "physical_location_identifier": (
            r"locationid", r"siteid", r"camerastation", r"stationid", r"plotid"
        ),
        "study_or_project_identifier": (
            r"studyid", r"studyarea", r"projectid", r"project", r"datasetid"
        ),
        "camera_or_device_identifier": (
            r"cameraid", r"deviceid", r"sensorid"
        ),
        "camera_model_or_make": (
            r"cameramodel", r"cameramake", r"camera.*brand", r"model"
        ),
        "deployment_start": (
            r"deployment.*start", r"deployment.*begin", r"startdate", r"begindate"
        ),
        "deployment_end": (
            r"deployment.*end", r"deployment.*retriev", r"enddate", r"retrievaldate"
        ),
        "event_date_or_datetime": (
            r"eventdatetime", r"datetime", r"photodate", r"observationdate", r"date"
        ),
        "event_time": (
            r"eventtime", r"phototime", r"observationtime", r"time"
        ),
        "taxon_identity_field": (
            r"scientificname", r"species", r"taxon", r"commonname"
        ),
        "detection_distance_or_calibration": (
            r"detectiondistance", r"triggerdistance", r"calibration.*distance",
            r"detection.*radius", r"detection.*angle", r"fieldofview",
            r"fov", r"distance.*calibr"
        ),
        "sampling_occasion_or_sequence": (
            r"occasion", r"sequenceid", r"eventid"
        ),
    }
    out: dict[str, list[str]] = {}
    for concept, regs in patterns.items():
        matched: list[str] = []
        for original in header:
            norm = _normalize(original)
            if any(re.search(reg, norm) for reg in regs):
                matched.append(original)
        out[concept] = matched
    return out


def _parse_header(raw: bytes, max_header_bytes: int) -> tuple[list[str], str]:
    if len(raw) > max_header_bytes:
        raise ValueError("header exceeds frozen maximum")
    if not raw.endswith((b"\n", b"\r")):
        raise ValueError("no complete newline-terminated header within frozen byte range")
    try:
        line = raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("header is not strict UTF-8/UTF-8-BOM") from exc
    rows = list(csv.reader([line.rstrip("\r\n")]))
    if len(rows) != 1 or not rows[0]:
        raise ValueError("CSV header parse failed")
    header = rows[0]
    if any(not cell.strip() for cell in header):
        raise ValueError("blank header field")
    digest = hashlib.sha256(raw).hexdigest()
    return header, digest


def _transport_stop(contract: dict, reason: str, http_status: int | None) -> dict:
    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "kays41_emammal_team_2020",
        "precheck_id": "e5-kays41-spatial-raw-header-result-v1",
        "status": "E5_RESPONSE_BLIND_RAW_HEADER_TRANSPORT_STOP",
        "source": {
            "dataset_doi": contract["source"]["dataset_doi"],
            "dryad_file_id": contract["source"]["dryad_file_id"],
            "file_name": contract["source"]["file_name"],
            "http_status": http_status,
        },
        "transport_stop_reason": reason,
        "response_boundary": {
            "header_lines_read": 0,
            "data_rows_read": 0,
            "response_values_read": 0,
            "species_values_read": 0,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "same_authorization_rerun_allowed": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    }


def _fetch_header(contract: dict) -> tuple[bytes | None, dict | None]:
    t = contract["transport_contract"]
    req = urllib.request.Request(
        contract["source"]["public_download_url"],
        headers={
            "Range": t["range_header"],
            "User-Agent": "esdm-e5-response-blind-header-precheck/1.0",
            "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = getattr(resp, "status", None)
            if status not in t["accepted_http_status"]:
                return None, _transport_stop(
                    contract,
                    "server did not return frozen partial-content status; body not read",
                    status,
                )
            raw = resp.readline(int(t["maximum_header_bytes"]) + 1)
    except urllib.error.HTTPError as exc:
        return None, _transport_stop(
            contract, "HTTP transport failed before header read", int(exc.code)
        )
    except urllib.error.URLError:
        return None, _transport_stop(
            contract, "URL transport failed before header read", None
        )
    return raw, None


def precheck(contract_path: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Kays41 raw-header contract")
    if contract["response_firewall"].get("data_row_read_authorized") is not False:
        raise ValueError("data-row firewall drifted")
    if contract["transport_contract"].get("http_range_required") is not True:
        raise ValueError("HTTP range must remain mandatory")
    if contract["transport_contract"].get("accepted_http_status") != [206]:
        raise ValueError("only HTTP 206 may expose the header")

    raw, stop = _fetch_header(contract)
    if stop is not None:
        return stop
    assert raw is not None

    try:
        header, digest = _parse_header(
            raw, int(contract["transport_contract"]["maximum_header_bytes"])
        )
    except ValueError as exc:
        return _transport_stop(contract, str(exc), 206)

    concepts = _match_concepts(header)
    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "kays41_emammal_team_2020",
        "precheck_id": "e5-kays41-spatial-raw-header-result-v1",
        "status": "E5_RESPONSE_BLIND_RAW_HEADER_PRECHECK",
        "source": {
            "dataset_doi": contract["source"]["dataset_doi"],
            "dryad_file_id": contract["source"]["dryad_file_id"],
            "file_name": contract["source"]["file_name"],
            "header_sha256": digest,
            "column_count": len(header),
        },
        "schema_concepts": {
            key: {
                "present": bool(matches),
                "matched_field_names": matches,
            }
            for key, matches in concepts.items()
        },
        "response_boundary": {
            "header_lines_read": 1,
            "data_rows_read": 0,
            "response_values_read": 0,
            "species_values_read": 0,
            "focal_response_opened": False,
        },
        "gate_hints": {
            "G2_SCHEMA_EFFORT_TIME": "SCHEMA_SUPPORT_ONLY_HEADER_CANNOT_PASS_G2",
            "G3_CROSSED_DOMAIN": (
                "SOURCE_PROTOCOL_FIELD_POTENTIAL"
                if concepts["study_or_project_identifier"]
                else "NO_SOURCE_PROTOCOL_FIELD_SEEN_IN_HEADER"
            ),
            "G4_DETECTION_IDENTIFIABILITY": (
                "CALIBRATION_FIELD_POTENTIAL_REQUIRES_SEPARATE_VALUE_LINKAGE_CONTRACT"
                if concepts["detection_distance_or_calibration"]
                else "NO_DIRECT_CALIBRATION_FIELD_SEEN_IN_HEADER"
            ),
        },
        "decision": {
            "candidate_qualified": False,
            "same_authorization_rerun_allowed": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "separate_child_contract_required_before_any_data_row_or_field_value": True,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = precheck(args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
