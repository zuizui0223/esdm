#!/usr/bin/env python3
"""Header-only response-blind precheck for the Wolfson wild-pig GPS/camera candidate."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

EXPECTED_CONTRACT_ID = "e5-wildpig-gps-camera-header-response-blind-v1"


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _has(headers: list[str], patterns: tuple[str, ...]) -> bool:
    values = [_norm(x) for x in headers]
    return any(
        p == h or (len(p) >= 3 and p in h)
        for h in values
        for p in patterns
    )


def fetch_prefix(url: str, max_bytes: int) -> bytes:
    req = Request(
        url,
        headers={
            "Range": f"bytes=0-{max_bytes - 1}",
            "User-Agent": "esdm-e5-response-blind-header/1",
            "Accept": "text/plain,text/csv,*/*",
        },
    )
    with urlopen(req, timeout=30) as response:
        status = getattr(response, "status", None)
        content_range = response.headers.get("Content-Range", "")
        if status != 206 and not content_range.lower().startswith("bytes "):
            raise ValueError("server did not honor bounded Range request")
        data = response.read(max_bytes)
        if len(data) > max_bytes:
            raise ValueError("range reader exceeded frozen byte bound")
        return data


def _header_from_prefix(prefix: bytes) -> list[str]:
    line = prefix.split(b"\n", 1)[0]
    if not line:
        raise ValueError("empty CSV header")
    if b"\n" not in prefix:
        raise ValueError("header exceeds frozen byte bound; fail closed")
    text = line.decode("utf-8-sig", errors="strict").rstrip("\r")
    return next(csv.reader([text]))


def precheck(
    contract: dict,
    fetcher: Callable[[str, int], bytes] = fetch_prefix,
) -> dict[str, object]:
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected wild-pig header contract")

    fw = contract["response_firewall"]
    if fw.get("first_csv_line_decode_authorized") is not True:
        raise ValueError("header decode not authorized")
    for key in (
        "second_csv_line_or_later_decode_authorized",
        "data_rows_read_authorized",
        "camera_detection_values_authorized",
        "gps_location_values_authorized",
        "gps_activity_or_movement_values_authorized",
        "timestamp_values_authorized",
        "effect_direction_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    max_bytes = int(fw["http_range_max_bytes"])
    results = []
    for spec in contract["source"]["seasonal_files"]:
        prefix = fetcher(spec["raw_url"], max_bytes)
        headers = _header_from_prefix(prefix)
        method = spec["method"]
        if method == "camera":
            flags = {
                "site_or_camera_id": _has(
                    headers,
                    ("camera", "camera_id", "station", "site", "location", "trap", "point"),
                ),
                "event_time": _has(
                    headers,
                    ("datetime", "date_time", "timestamp", "date", "time"),
                ),
            }
        elif method == "gps":
            flags = {
                "individual_or_collar_id": _has(
                    headers,
                    ("animal", "individual", "collar", "pig", "id"),
                ),
                "event_time": _has(
                    headers,
                    ("datetime", "date_time", "timestamp", "date", "time"),
                ),
                "activity_or_movement_axis": _has(
                    headers,
                    (
                        "activity", "speed", "movement", "step", "distance",
                        "latitude", "longitude", "lat", "lon", "x", "y",
                        "easting", "northing",
                    ),
                ),
            }
        else:
            raise ValueError(f"unexpected method: {method}")

        results.append(
            {
                "geography": spec["geography"],
                "method": method,
                "season": spec["season"],
                "path": spec["path"],
                "header_column_count": len(headers),
                "headers": headers,
                "schema_flags": flags,
                "bytes_received_max": max_bytes,
                "decoded_lines": 1,
                "data_rows_decoded": 0,
            }
        )

    camera = [r for r in results if r["method"] == "camera"]
    gps = [r for r in results if r["method"] == "gps"]
    camera_viable = all(
        r["schema_flags"]["site_or_camera_id"] and r["schema_flags"]["event_time"]
        for r in camera
    )
    gps_viable = all(
        r["schema_flags"]["individual_or_collar_id"]
        and r["schema_flags"]["event_time"]
        and r["schema_flags"]["activity_or_movement_axis"]
        for r in gps
    )

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "wolfson_wildpig_gps_camera_2015_2018",
        "precheck_id": "e5-wildpig-gps-camera-header-result-v1",
        "status": "E5_RESPONSE_BLIND_HEADER_PRECHECK",
        "files": results,
        "schema_summary": {
            "camera_files_checked": len(camera),
            "gps_files_checked": len(gps),
            "geographies": sorted({r["geography"] for r in results}),
            "seasons": sorted({r["season"] for r in results}),
            "camera_schema_viable_all_files": camera_viable,
            "gps_external_activity_schema_viable_all_files": gps_viable,
            "crossed_method_geography_file_geometry_preserved": True,
        },
        "response_boundary": {
            "files_header_checked": len(results),
            "maximum_bytes_requested_per_file": max_bytes,
            "decoded_header_lines": len(results),
            "data_rows_decoded": 0,
            "camera_detection_values_read": 0,
            "gps_location_or_activity_values_read": 0,
            "timestamp_values_read": 0,
            "effect_direction_read": False,
            "focal_response_opened": False,
        },
        "decision": {
            "candidate_qualified": False,
            "G2_pass_authorized": False,
            "final_G4_pass_authorized": False,
            "value_blind_child_contract_recommended": bool(camera_viable and gps_viable),
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    value = precheck(contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
