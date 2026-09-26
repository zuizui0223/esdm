#!/usr/bin/env python3
"""Open the final Snapshot Japan Camtrap DP response exactly once, without fitting."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from esdm.validate.empirical_snapshot_japan_camtrapdp import (
    build_snapshot_japan_empirical_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "empirical" / "SNAPSHOT_JAPAN_CAMTRAPDP_FINAL_CONTRACT.json"


def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--climate", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-output", required=True)
    return parser


def _get(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "esdm-r5b-snapshot-japan-camtrapdp-final/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
        return response.read()


def main() -> int:
    args = _parser().parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    climate = json.loads(Path(args.climate).read_text(encoding="utf-8"))
    output = Path(args.output)
    source_output = Path(args.source_output)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_output.parent.mkdir(parents=True, exist_ok=True)

    base = {
        "schema": "esdm.empirical_r5b.snapshot_japan_camtrapdp_capture.v1",
        "status": "STOP_PRE_RESPONSE_TRANSPORT",
        "contract_id": contract["contract_id"],
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        expected_cache = contract["climate_input"]["camera_climate_sha256"]
        if climate.get("status") != "CLIMATE_QUALIFIED":
            raise RuntimeError("frozen climate artifact is not qualified")
        if climate.get("camera_climate_sha256") != expected_cache:
            raise RuntimeError("frozen climate cache hash mismatch")

        payload = _get(contract["source"]["url"])
    except Exception as exc:
        result = {
            **base,
            "response_bytes_opened": 0,
            "response_rows_opened": 0,
            "response_values_opened": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    source_output.write_bytes(payload)
    source_md5 = hashlib.md5(payload).hexdigest()  # noqa: S324 provenance only
    source_sha256 = hashlib.sha256(payload).hexdigest()
    if source_md5 != contract["source"]["md5"]:
        result = {
            **base,
            "status": "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY",
            "response_bytes_opened": len(payload),
            "response_rows_opened": "unknown_after_full_archive_capture",
            "response_values_opened": True,
            "source_md5": source_md5,
            "source_sha256": source_sha256,
            "reason": "Camtrap DP source MD5 drift",
        }
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 1

    stops = contract["consumed_estimability_stops"]
    try:
        fixture = build_snapshot_japan_empirical_fixture(
            camtrapdp_zip=payload,
            climate_payload=climate,
            expected_md5=contract["source"]["md5"],
            expected_deployment_count=contract["spatial_contract"]["expected_deployment_count"],
            minimum_role_count=contract["training_stream_partition"]["minimum_training_deployments_each_stream"],
            minimum_training_state_count=stops["minimum_training_state_annotated_each_state"],
            minimum_calibration_state_count=stops["minimum_state_calibration_each_state"],
            minimum_heldout_state_count=stops["minimum_heldout_state_annotated_each_state"],
        )
        diagnostics = dict(fixture.diagnostics)
        presence = diagnostics["presence_event_totals"]
        if presence["presence_opportunistic"] < stops["minimum_opportunistic_focal_events"]:
            raise ValueError("opportunistic focal-event minimum not met")
        if presence["presence_calibrated"] < stops["minimum_calibrated_focal_events"]:
            raise ValueError("calibrated focal-event minimum not met")
    except Exception as exc:
        result = {
            **base,
            "status": "CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY",
            "response_bytes_opened": len(payload),
            "response_rows_opened": "full observations.csv parsed",
            "response_values_opened": True,
            "source_md5": source_md5,
            "source_sha256": source_sha256,
            "reason": f"{type(exc).__name__}: {exc}",
        }
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    result = {
        **base,
        "status": "RESPONSE_CAPTURE_QUALIFIED",
        "response_bytes_opened": len(payload),
        "response_rows_opened": "full observations.csv parsed",
        "response_values_opened": True,
        "source_md5": source_md5,
        "source_sha256": source_sha256,
        "climate_camera_sha256": fixture.climate_sha256,
        "diagnostics": diagnostics,
        "train_space_count": len(fixture.train_spaces),
        "heldout_space_count": len(fixture.heldout_spaces),
        "next_stage": "pin this capture artifact and run the already-frozen three-fit empirical endpoint without another external response GET"
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
