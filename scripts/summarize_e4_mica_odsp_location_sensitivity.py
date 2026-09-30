#!/usr/bin/env python3
"""Summarize E4 physical-location-block ODSP sensitivity."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


EXPECTED_BLOCKS = 27
EXPECTED_ROWS = 733
EXPECTED_ACTIVITY_GAIN = -0.6390511804117178
EXPECTED_STATE_GAIN = 0.008390925023042506
TOL = 1e-12


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("receipt must be a JSON object")
    return value


def _axis(name, receipt, expected_gain):
    certification = receipt["certified_result"]["certification"]
    steps = certification["steps"]
    if len(steps) != 1:
        raise ValueError(f"{name} sensitivity requires one transfer step")
    step = steps[0]
    groups = step["groups"]
    if len(groups) != 1:
        raise ValueError(f"{name} sensitivity requires one endpoint group")
    cell = groups[0]
    if cell["group"] != "MICA_MUSKRAT":
        raise ValueError(f"{name} endpoint group drifted")
    if int(cell["row_count"]) != EXPECTED_ROWS:
        raise ValueError(f"{name} row count drifted")
    if int(cell["block_count"]) != EXPECTED_BLOCKS:
        raise ValueError(f"{name} physical-location block count drifted")
    if cell["estimable"] is not True:
        raise ValueError(f"{name} location-block sensitivity must be estimable")
    gain = float(cell["mean_gain"])
    if not math.isclose(gain, expected_gain, rel_tol=0.0, abs_tol=TOL):
        raise ValueError(f"{name} frozen point gain drifted")
    population = receipt["population_result"]
    if int(population["group_count"]) != 1:
        raise ValueError(f"{name} population_result must retain one endpoint group")
    if population["familywise_confirmatory_claim"] is not False:
        raise ValueError(f"{name} sensitivity must remain descriptive")
    return {
        "endpoint_id": receipt["endpoint_id"],
        "point_mean_gain": gain,
        "point_gain_identity_passed": True,
        "certified_category": step["category"],
        "certified_group_status": cell["status"],
        "certified_lower_bound": float(cell["lower_bound"]),
        "certified_upper_bound": float(cell["upper_bound"]),
        "point_transfer_ceiling": certification["point_transfer_ceiling"],
        "certified_transfer_ceiling": certification["certified_transfer_ceiling"],
        "row_count": int(cell["row_count"]),
        "physical_location_block_count": int(cell["block_count"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activity-receipt", type=Path, required=True)
    parser.add_argument("--state-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "schema_version": 1,
        "sensitivity_id": "e4-mica-odsp-location-block-sensitivity-result-v1",
        "status": "POSTRESULT_DESCRIPTIVE_SENSITIVITY",
        "activity": _axis(
            "activity", _read(args.activity_receipt), EXPECTED_ACTIVITY_GAIN
        ),
        "state": _axis(
            "state", _read(args.state_receipt), EXPECTED_STATE_GAIN
        ),
        "boundary": {
            "official_733_deployment_block_audit_replaced": False,
            "frozen_e4_decision_changed": False,
            "superpopulation_interpretation_authorized": False,
            "n3_handoff_authorized": False,
            "confirmatory_claim": False,
            "causal_claim": False,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "activity_category": result["activity"]["certified_category"],
        "activity_interval": [
            result["activity"]["certified_lower_bound"],
            result["activity"]["certified_upper_bound"],
        ],
        "state_category": result["state"]["certified_category"],
        "state_interval": [
            result["state"]["certified_lower_bound"],
            result["state"]["certified_upper_bound"],
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
