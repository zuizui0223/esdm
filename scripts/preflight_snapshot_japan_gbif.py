#!/usr/bin/env python3
"""HEAD-only source-archive transport preflight for Snapshot Japan."""

from __future__ import annotations

import json
from pathlib import Path
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_JAPAN_GBIF_TRANSPORT_CONTRACT.json"
OUTPUT = ROOT / "artifacts" / "snapshot_japan_gbif_transport.json"


class HeadOnlyHandler(urllib.request.HTTPRedirectHandler):
    pass


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    cfg = contract["transport"]
    url = contract["dataset"]["source_archive_url"]
    base = {
        "schema": "esdm.empirical_r5b.snapshot_japan_gbif_transport_result.v1",
        "status": "STOP_PRE_RESPONSE_SOURCE_ARCHIVE_TRANSPORT",
        "request_method": "HEAD",
        "request_count": 1,
        "response_payload_bytes": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "species_values_opened": False,
        "age_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "esdm-r5b-snapshot-japan-gbif-head/1.0"},
            method="HEAD",
        )
        opener = urllib.request.build_opener(HeadOnlyHandler())
        with opener.open(request, timeout=90) as response:  # noqa: S310
            status = int(response.status)
            final_url = response.geturl()
            headers = dict(response.headers.items())

        host = urllib.parse.urlparse(final_url).hostname
        content_length_raw = headers.get("Content-Length")
        content_length = (
            int(content_length_raw)
            if content_length_raw is not None
            else None
        )
        if bool(cfg["require_http_200"]) and status != 200:
            raise RuntimeError(f"HEAD returned HTTP {status}")
        if host not in set(cfg["allowed_final_hosts"]):
            raise RuntimeError(f"unexpected final host {host!r}")
        if bool(cfg["require_positive_content_length"]) and (
            content_length is None or content_length <= 0
        ):
            raise RuntimeError("HEAD did not provide positive Content-Length")

        result = {
            **base,
            "status": "SOURCE_ARCHIVE_TRANSPORT_QUALIFIED",
            "http_status": status,
            "final_url": final_url,
            "final_host": host,
            "content_length": content_length,
            "content_type": headers.get("Content-Type"),
            "etag": headers.get("ETag"),
            "last_modified": headers.get("Last-Modified"),
        }
    except Exception as exc:
        result = {
            **base,
            "reason": f"{type(exc).__name__}: {exc}",
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
