#!/usr/bin/env python3
"""Response-blind existence/transport preflight for LILA Serengeti JSON metadata.

HTTP HEAD only. This intentionally cannot download biological records.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SEASONS = (1, 6, 11)
BASE = ("https://lilawildlife.blob.core.windows.net/"
        "lila-wildlife/snapshotserengeti-v-2-0/")


def metadata_url(season: int) -> str:
    if not 1 <= season <= 11:
        raise ValueError("invalid season index")
    return f"{BASE}SnapshotSerengetiS{season:02d}.json.zip"


def head_one(season: int, timeout=20, opener=urlopen):
    req = Request(metadata_url(season), method="HEAD",
                  headers={"User-Agent": "esdm-E7-responseblind-metadata-check/1.0"})
    try:
        with opener(req, timeout=timeout) as response:
            headers = response.info()
            status = getattr(response, "status", response.getcode())
            n = headers.get("Content-Length", "")
            n = int(n) if n.isdecimal() else None
            return {
                "season": season, "url": metadata_url(season),
                "status": "ACCESSIBLE_HEADERS_ONLY" if status == 200 else "TRANSPORT_HTTP_UNEXPECTED",
                "http_status": status, "content_bytes_reported": n,
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
            }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "season": season, "url": metadata_url(season),
            "status": "TRANSPORT_UNAVAILABLE",
            "http_status": getattr(exc, "code", None),
            "error_class": type(exc).__name__,
        }


def run(opener=urlopen):
    records = [head_one(n, opener=opener) for n in SEASONS]
    ok = all(r["status"] == "ACCESSIBLE_HEADERS_ONLY" and
             (r["content_bytes_reported"] is None or
              r["content_bytes_reported"] > 0) for r in records)
    return {
        "status": "RESPONSE_BLIND_HEAD_PASS" if ok else "RESPONSE_BLIND_TRANSPORT_STOP",
        "probe_seasons": list(SEASONS),
        "records": records,
        "biological_bytes_downloaded": 0,
        "source_json_rows_read": 0,
        "permission_to_tune_analysis_after_result": False,
        "frozen_design": "docs/replication/E7_SERENGETI_WET_DRY_COMMUNITY_FROZEN_DESIGN.md",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result))
    if result["status"] != "RESPONSE_BLIND_HEAD_PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
