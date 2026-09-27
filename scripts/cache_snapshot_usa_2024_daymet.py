#!/usr/bin/env python3
"""Cache frozen Daymet precipitation for a qualified Snapshot USA header result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from esdm.validate.empirical_snapshot_usa_daymet import (
    build_precipitation_covariate_table,
    daymet_site_request,
)


USER_AGENT = "esdm-r5b-snapshot-usa-daymet/1.0"


def _download(url: str, *, attempts: int = 3) -> bytes:
    last = None
    for attempt in range(attempts):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
                },
            )
            with urlopen(request, timeout=90) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"Daymet download failed after {attempts} attempts: {last}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    header = json.loads(args.header_result.read_text(encoding="utf-8"))
    if header.get("status") != "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED":
        raise ValueError("Snapshot USA header result is not qualified")
    if header.get("response_rows_opened") != 0:
        raise ValueError("Snapshot USA response rows were already opened")
    if header.get("response_values_opened") is not False:
        raise ValueError("Snapshot USA response values were already opened")
    if header.get("model_fits") != 0 or header.get("heldout_scores") != 0:
        raise ValueError("Snapshot USA header stage already ran scientific analysis")

    deployment = header.get("deployment")
    if not isinstance(deployment, dict):
        raise ValueError("qualified header result lacks deployment metadata")
    selected_sites = deployment.get("selected_sites")
    selected_deployments = deployment.get("selected_deployments")
    if not isinstance(selected_sites, list) or len(selected_sites) != 64:
        raise ValueError("qualified header result must contain 64 selected_sites")
    if not isinstance(selected_deployments, list) or not selected_deployments:
        raise ValueError("qualified header result lacks selected_deployments")

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    raw_by_site = {}
    requests = []
    for row in selected_sites:
        request = daymet_site_request(
            row["spatial_unit"],
            row["latitude"],
            row["longitude"],
        )
        requests.append(request)
        raw = _download(request.url)
        raw_by_site[request.spatial_unit] = raw
        (args.cache_dir / request.cache_filename).write_bytes(raw)

    result = build_precipitation_covariate_table(
        selected_sites=selected_sites,
        selected_deployments=selected_deployments,
        raw_by_spatial_unit=raw_by_site,
    )
    result["source_header_result"] = {
        "contract_id": header.get("contract_id"),
        "deployment_sha256": deployment.get("sha256"),
        "sequence_header_sha256": (
            header.get("sequence_header", {}).get("header_sha256")
            if isinstance(header.get("sequence_header"), dict)
            else None
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "selected_site_count": result["cache_manifest"]["selected_site_count"],
                "context_count": result["context_count"],
                "training_context_count": result["training_context_count"],
                "heldout_context_count": result["heldout_context_count"],
                "manifest_sha256": result["cache_manifest_sha256"],
                "table_sha256": result["table_sha256"],
                "response_rows_opened": result["response_rows_opened"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
