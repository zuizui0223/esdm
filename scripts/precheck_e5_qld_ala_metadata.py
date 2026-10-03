#!/usr/bin/env python3
"""Summarize one public ALA dataResource metadata response without following data links."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


SAFE_TOP_LEVEL = (
    "uid",
    "name",
    "acronym",
    "websiteUrl",
    "pubDescription",
    "dataProviderUid",
    "institutionUid",
    "rights",
    "licenseType",
    "dateCreated",
    "lastUpdated",
)

URL_KEY_FRAGMENTS = ("url", "uri", "link", "endpoint", "source", "archive", "download")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value.strip())
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _collect_url_like(value: object, *, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if _is_http_url(child):
                found.append({"path": child_path, "url": str(child)})
            elif isinstance(child, (dict, list)):
                found.extend(_collect_url_like(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            if _is_http_url(child):
                found.append({"path": child_path, "url": str(child)})
            elif isinstance(child, (dict, list)):
                found.extend(_collect_url_like(child, path=child_path))
    return found


def summarize(metadata_path: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "e5-qld-ala-dataresource-metadata-only-v1":
        raise ValueError("unexpected ALA metadata contract")

    firewall = contract["response_firewall"]
    for key in (
        "occurrence_api_query_authorized",
        "image_api_query_authorized",
        "media_download_authorized",
        "gbif_occurrence_download_authorized",
        "dataset_archive_download_authorized",
        "camtrapdp_package_download_authorized",
        "deployment_rows_read_authorized",
        "observation_rows_read_authorized",
        "species_fields_read_authorized",
        "focal_response_opening_authorized",
        "model_fitting_authorized",
    ):
        if firewall.get(key) is not False:
            raise ValueError(f"response firewall drifted: {key}")

    raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("ALA dataResource metadata must be a JSON object")

    uid = str(raw.get("uid", ""))
    if uid and uid != contract["source"]["ala_data_resource_uid"]:
        raise ValueError(f"ALA dataResource uid drifted: {uid}")

    safe = {}
    for key in SAFE_TOP_LEVEL:
        value = raw.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value

    connection = raw.get("connectionParameters")
    connection_keys = sorted(connection) if isinstance(connection, dict) else []

    data_links = []
    for row in raw.get("dataLinks", []) if isinstance(raw.get("dataLinks"), list) else []:
        if not isinstance(row, dict):
            continue
        item = {}
        for key in ("name", "type", "description", "url", "uri"):
            value = row.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                item[key] = value
        if item:
            data_links.append(item)

    external = []
    for row in raw.get("externalIdentifiers", []) if isinstance(raw.get("externalIdentifiers"), list) else []:
        if not isinstance(row, dict):
            continue
        item = {}
        for key in ("provider", "identifier", "id", "url"):
            value = row.get(key)
            if isinstance(value, (str, int, float, bool)) or value is None:
                item[key] = value
        if item:
            external.append(item)

    url_like = _collect_url_like(raw)
    # De-duplicate deterministically without following any URL.
    seen = set()
    urls = []
    for item in sorted(url_like, key=lambda x: (x["path"], x["url"])):
        pair = (item["path"], item["url"])
        if pair in seen:
            continue
        seen.add(pair)
        urls.append(item)

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "qld_wet_tropics_camtrapdp_2022_2023",
        "precheck_id": "e5-qld-ala-dataresource-metadata-result-v1",
        "status": "E5_RESPONSE_BLIND_ALA_METADATA_PRECHECK",
        "source": {
            "endpoint": contract["source"]["metadata_endpoint"],
            "raw_metadata_sha256": _sha256(metadata_path),
        },
        "safe_metadata": safe,
        "connection_parameters": {
            "present": isinstance(connection, dict),
            "keys_only": connection_keys,
        },
        "data_links": data_links,
        "external_identifiers": external,
        "url_like_values": urls,
        "response_boundary": {
            "metadata_json_objects_read": 1,
            "discovered_urls_followed": 0,
            "dataset_archive_downloaded": False,
            "deployment_rows_read": 0,
            "observation_rows_read": 0,
            "media_rows_read": 0,
            "species_fields_read": 0,
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
            "separate_child_contract_required_before_following_any_discovered_url": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    value = summarize(args.metadata, args.contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
