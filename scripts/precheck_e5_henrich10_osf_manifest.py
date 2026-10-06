#!/usr/bin/env python3
"""Response-blind OSF manifest reader for the Henrich10 E5 candidate.

Only OSF API metadata are requested. File download/render/preview links are never
followed, and no file body is opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

EXPECTED_CONTRACT_ID = "e5-henrich10-osf-manifest-response-blind-v1"
NODE_ID = "3vwkq"
API_HOST = "api.osf.io"
API_PATH_PREFIX = f"/v2/nodes/{NODE_ID}/"

HINT_GROUPS = {
    "effort": (
        "effort", "deployment", "camera", "site", "station", "timelapse", "time_lapse"
    ),
    "reference_calibration": (
        "calibration", "reference", "ranging", "range_pole", "ranging_pole", "mask"
    ),
    "ctds_radial_distance": (
        "ctds", "radial", "animal_distance", "observation_distance",
        "distance_estimate", "distance_estimates", "detection_function"
    ),
}


def _assert_metadata_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != API_HOST:
        raise ValueError(f"non-OSF-API URL rejected: {url}")
    if not parsed.path.startswith(API_PATH_PREFIX):
        raise ValueError(f"out-of-scope OSF API path rejected: {url}")
    lowered = url.lower()
    for token in ("/download", "/render", "/preview"):
        if token in lowered:
            raise ValueError(f"content-bearing route rejected: {url}")


def fetch_json(url: str) -> dict:
    _assert_metadata_url(url)
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.api+json",
            "User-Agent": "esdm-e5-response-blind-manifest/1",
        },
    )
    with urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            raise ValueError(f"non-JSON OSF metadata response: {content_type}")
        return json.loads(response.read().decode("utf-8"))


def _hints(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        group: any(token in lowered for token in tokens)
        for group, tokens in HINT_GROUPS.items()
    }


def build_manifest(
    contract: dict,
    getter: Callable[[str], dict] = fetch_json,
) -> dict:
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected Henrich10 manifest contract")

    fw = contract["response_firewall"]
    required_true = (
        "project_metadata_read_authorized",
        "storage_manifest_metadata_read_authorized",
        "recursive_folder_manifest_read_authorized",
    )
    required_false = (
        "file_content_read_authorized",
        "file_download_authorized",
        "file_preview_authorized",
        "biological_rows_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    )
    for key in required_true:
        if fw.get(key) is not True:
            raise ValueError(f"required manifest authorization missing: {key}")
    for key in required_false:
        if fw.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    requested_urls: list[str] = []

    def get(url: str) -> dict:
        _assert_metadata_url(url)
        requested_urls.append(url)
        return getter(url)

    node_url = contract["source"]["node_api"]
    root_url = contract["source"]["osfstorage_api"] + "?page[size]=100"
    node_payload = get(node_url)
    node_data = node_payload.get("data", {})
    node_attributes = node_data.get("attributes", {})

    entries: list[dict[str, object]] = []
    queue = [root_url]
    seen_urls: set[str] = set()

    while queue:
        url = queue.pop(0)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        payload = get(url)
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            kind = attrs.get("kind")
            name = str(attrs.get("name") or "")
            materialized_path = str(attrs.get("materialized_path") or name)
            entry = {
                "id": str(item.get("id") or ""),
                "guid": attrs.get("guid"),
                "name": name,
                "kind": kind,
                "materialized_path": materialized_path,
                "size": attrs.get("size"),
                "current_version": attrs.get("current_version"),
                "date_modified": attrs.get("date_modified"),
                "provider": attrs.get("provider"),
                "hints": _hints(materialized_path),
            }
            entries.append(entry)
            if kind == "folder":
                folder_id = quote(str(item.get("id") or ""), safe="")
                if not folder_id:
                    raise ValueError("folder missing OSF file id")
                queue.append(
                    f"https://api.osf.io/v2/nodes/{NODE_ID}/files/"
                    f"osfstorage/{folder_id}/?page[size]=100"
                )

        next_url = payload.get("links", {}).get("next")
        if next_url:
            _assert_metadata_url(next_url)
            queue.append(next_url)

    matched = {
        group: [
            e["materialized_path"]
            for e in entries
            if e["hints"].get(group)
        ]
        for group in HINT_GROUPS
    }

    decision = {
        "manifest_supports_effort_child": bool(matched["effort"]),
        "manifest_supports_reference_calibration_child": bool(
            matched["reference_calibration"]
        ),
        "manifest_supports_ctds_radial_distance_child": bool(
            matched["ctds_radial_distance"]
        ),
        "child_contract_recommended": bool(
            matched["effort"]
            and matched["reference_calibration"]
            and matched["ctds_radial_distance"]
        ),
        "candidate_qualified": False,
        "G2_pass_authorized": False,
        "final_G4_pass_authorized": False,
        "focal_response_opening_authorized": False,
        "model_fitting_authorized": False,
    }

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "henrich10_ctds_germany_2019_2020",
        "precheck_id": "e5-henrich10-osf-manifest-result-v1",
        "status": "E5_RESPONSE_BLIND_OSF_MANIFEST_PRECHECK",
        "project_metadata": {
            "node_id": NODE_ID,
            "title": node_attributes.get("title"),
            "category": node_attributes.get("category"),
            "date_modified": node_attributes.get("date_modified"),
            "public": node_attributes.get("public"),
        },
        "manifest": {
            "entry_count": len(entries),
            "file_count": sum(e["kind"] == "file" for e in entries),
            "folder_count": sum(e["kind"] == "folder" for e in entries),
            "entries": entries,
            "matched_path_hints": matched,
        },
        "response_boundary": {
            "metadata_requests_made": len(requested_urls),
            "requested_urls": requested_urls,
            "file_downloads_followed": 0,
            "file_previews_opened": 0,
            "file_contents_opened": 0,
            "biological_rows_read": 0,
            "focal_response_opened": False,
        },
        "decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    value = build_manifest(contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
