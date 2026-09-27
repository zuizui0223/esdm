#!/usr/bin/env python3
"""Run the frozen response-blind E2 MICA WorldClim BIO12 freeze."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.e2_mica_worldclim import freeze_e2_mica_worldclim


ROOT = Path(__file__).resolve().parents[1]
FROZEN_RESPONSE_BLIND = (
    ROOT
    / "docs"
    / "replication"
    / "E2_MICA_RESPONSE_BLIND_GEOMETRY_HEADER_RESULT.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mica-archive", type=Path, required=True)
    parser.add_argument("--worldclim-archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = json.loads(FROZEN_RESPONSE_BLIND.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    base = {
        "schema_version": 1,
        "result_id": "e2-mica-worldclim-bio12-v1",
        "status": "STOP_PRE_RESPONSE_CLIMATE_TRANSPORT_OR_SCHEMA",
        "candidate_id": "MICA_MUSKRAT",
        "response_firewall": {
            "scientific_name_values_read": False,
            "count_values_read": False,
            "observation_rows_read_for_climate": 0,
            "focal_taxon_filtering": False,
            "model_fits": 0,
            "heldout_scores": 0,
            "full_response_opened": False,
        },
    }
    try:
        result = freeze_e2_mica_worldclim(
            args.mica_archive,
            args.worldclim_archive,
            receipt,
        )
    except Exception as exc:
        result = {
            **base,
            "reason": f"{type(exc).__name__}: {exc}",
            "decision": {
                "climate_qualified": False,
                "authorizes_full_response": False,
                "requires_separate_full_response_authorization": True,
            },
        }

    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "training_count": result.get("training", {}).get("deployment_count"),
                "heldout_count": result.get("heldout_deployment_count"),
                "reason": result.get("reason"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
