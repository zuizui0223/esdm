#!/usr/bin/env python3
"""Response-blind ZIP-member and CSV-first-header check for Rhode Island cameras.

The ZIP is transported in full because Zenodo supplies one archive. No biological
record is selected, decoded, counted, modeled, or uploaded: only the ZIP directory
and the first header line of each of two predeclared CSV members are inspected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from typing import Callable
from urllib.request import Request, urlopen
import zipfile

EXPECTED_ID = "e5-rhode-island-paired-zip-header-response-blind-v1"
EXPECTED_URL = "https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
EXPECTED_BASENAMES = (
    "RI_CameraSurvey_Deployments.csv",
    "RI_CameraSurvey_Detections.csv",
)


def fetch_archive(url: str, expected_bytes: int) -> bytes:
    if url != EXPECTED_URL:
        raise ValueError("unfrozen archive URL")
    request = Request(url, headers={"User-Agent": "esdm-e5-zip-header-only/1"})
    with urlopen(request, timeout=120) as response:
        data = response.read(expected_bytes + 1)
    if len(data) != expected_bytes:
        raise ValueError("archive does not match frozen byte length")
    return data


def normalize(field: str) -> str:
    return re.sub(r"[^a-z0-9]", "", field.strip().casefold())


def has(headers: list[str], patterns: tuple[str, ...]) -> bool:
    return any(
        (h == token or (len(token) >= 4 and token in h))
        for h in map(normalize, headers)
        for token in patterns
    )


def schema_flags(kind: str, headers: list[str]) -> dict[str, bool]:
    site = has(
        headers, ("site", "siteid", "location", "locationid", "station", "stationid")
    )
    camera = has(
        headers,
        ("camera", "cameraid", "camid", "camerano", "cameraidentifier", "deviceid"),
    )
    if kind == "deployment":
        start = has(
            headers, ("start", "begin", "setup", "deploydate", "startdatetime")
        )
        end = has(
            headers, ("end", "retrieval", "removed", "enddatetime", "stopdate")
        )
        lat = has(headers, ("latitude", "lat"))
        lon = has(headers, ("longitude", "lon", "lng"))
        region = has(headers, ("region", "section", "eastwest", "surveyarea"))
        period = has(
            headers, ("yearseason", "surveyseason", "season", "year", "period")
        )
        return {
            "site_id_named": site,
            "camera_id_named": camera,
            "start_named": start,
            "end_named": end,
            "geography_named": (lat and lon) or region,
            "survey_period_named": period,
        }
    if kind == "detection":
        event_time = has(
            headers, ("datetime", "timestamp", "imagetime", "time", "date")
        )
        taxon = has(
            headers, ("species", "scientificname", "taxon", "commonname")
        )
        period = has(
            headers, ("yearseason", "surveyseason", "season", "year", "period")
        )
        return {
            "site_id_named": site,
            "camera_id_named": camera,
            "event_time_named": event_time,
            "taxon_field_named": taxon,
            "survey_period_named": period,
        }
    raise ValueError("unexpected kind")


def read_csv_first_header(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
    bound: int,
) -> list[str]:
    with archive.open(member, "r") as stream:
        header_line = stream.readline(bound)
    if not header_line.endswith(b"\n"):
        raise ValueError("CSV header exceeds frozen byte bound or lacks newline")
    # CRLF and an optional UTF-8 BOM are permitted. The rest of the CSV is
    # deliberately never passed to csv.reader or decoded.
    text = header_line.decode("utf-8-sig", errors="strict").rstrip("\r\n")
    headers = next(csv.reader([text], strict=True))
    if not headers or len(set(headers)) != len(headers):
        raise ValueError("CSV header is empty or contains duplicate fields")
    return headers


def inspect(
    contract: dict,
    fetcher: Callable[[str, int], bytes] = fetch_archive,
) -> dict:
    if contract.get("contract_id") != EXPECTED_ID:
        raise ValueError("unfrozen contract id")
    if contract.get("status") != "FROZEN_ZIP_MEMBER_HEADER_PRECHECK_NOT_AUTHORIZED":
        raise ValueError("contract freeze drift")
    fw = contract["response_firewall"]
    if fw.get("decode_only_first_CSV_header_line_of_2_pinned_members") is not True:
        raise ValueError("header-only authorization absent")
    for key in (
        "unzip_or_save_entire_members_authorized",
        "inspect_CSV_data_rows_authorized",
        "inspect_species_values_authorized",
        "inspect_event_time_values_authorized",
        "inspect_focal_diel_or_detection_counts_authorized",
        "model_fitting_authorized",
        "focal_response_opening_authorized",
        "upload_raw_ZIP_or_CSV_authorized",
    ):
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drift: {key}")
    src = contract["source"]
    expected_bytes = int(src["archive_bytes"])
    if expected_bytes != 12059878:
        raise ValueError("unexpected archive byte length")
    if src["required_CSV_member_basenames"] != list(EXPECTED_BASENAMES):
        raise ValueError("required member names drifted")
    blob = fetcher(src["archive_download_url"], expected_bytes)
    if len(blob) != expected_bytes:
        raise ValueError("archive byte count mismatch")
    md5 = hashlib.md5(blob).hexdigest()
    if md5 != src["archive_public_md5"]:
        raise ValueError("frozen Zenodo archive MD5 mismatch")

    result_members: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        infos = archive.infolist()
        if not infos or len(infos) > 2000:
            raise ValueError("unexpected archive directory size")
        selected: dict[str, zipfile.ZipInfo] = {}
        for member in infos:
            if member.is_dir():
                continue
            basename = PurePosixPath(member.filename).name
            for want in EXPECTED_BASENAMES:
                if basename.casefold() == want.casefold():
                    if want in selected:
                        raise ValueError("duplicate candidate CSV member basename")
                    selected[want] = member
        for basename, kind in (
            (EXPECTED_BASENAMES[0], "deployment"),
            (EXPECTED_BASENAMES[1], "detection"),
        ):
            if basename not in selected:
                result_members[kind] = {
                    "status": "REQUIRED_MEMBER_NOT_FOUND",
                    "basename": basename,
                    "headers": [],
                    "schema_flags": {},
                }
                continue
            member = selected[basename]
            fields = read_csv_first_header(
                archive,
                member,
                int(fw["compressed_CSV_stream_first_bytes_limit"]),
            )
            result_members[kind] = {
                "status": "CSV_HEADER_DECODED_ONLY",
                "basename": basename,
                "uncompressed_member_bytes_metadata": member.file_size,
                "headers": fields,
                "schema_flags": schema_flags(kind, fields),
            }
        archive_member_count = len(infos)

    complete = all(
        result_members[kind]["status"] == "CSV_HEADER_DECODED_ONLY"
        for kind in ("deployment", "detection")
    )
    d = result_members["deployment"]["schema_flags"]
    e = result_members["detection"]["schema_flags"]
    potential_join = bool(
        complete
        and d.get("site_id_named")
        and d.get("camera_id_named")
        and d.get("start_named")
        and d.get("end_named")
        and e.get("site_id_named")
        and e.get("camera_id_named")
        and e.get("event_time_named")
    )
    status = (
        "RESPONSE_BLIND_HEADER_ROUTE_PLAUSIBLE_UNQUALIFIED"
        if potential_join
        else "STOP_OR_HOLD_HEADER_SCHEMA_INCOMPLETE"
    )
    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "rhode_island_paired_cameras_2018_2023",
        "precheck_id": "e5-rhode-island-paired-zip-header-result-v1",
        "status": status,
        "zip_receipt": {
            "zenodo_record_id": src["zenodo_record_id"],
            "zip_byte_size": len(blob),
            "zip_md5": md5,
            "zip_directory_entries": archive_member_count,
        },
        "members": result_members,
        "response_boundary": {
            "full_archive_containing_biological_rows_transferred": True,
            "CSVs_whose_first_header_decoded": sum(
                r["status"] == "CSV_HEADER_DECODED_ONLY"
                for r in result_members.values()
            ),
            "decoded_biological_data_rows": 0,
            "species_values_inspected": False,
            "event_time_values_inspected": False,
            "focal_diel_outcomes_inspected": False,
            "model_fits_executed": 0,
            "uploaded_raw_ZIP_or_CSV": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "G3_pass_authorized": False,
            "G4_pass_authorized": False,
            "nominate_separate_deployment_geometry_child": potential_join,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(json.loads(args.contract.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
