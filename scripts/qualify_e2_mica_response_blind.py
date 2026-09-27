#!/usr/bin/env python3
"""Run the frozen response-blind E2 MICA geometry/header qualification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = qualify_e2_mica_archive(args.archive)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "result_id": "e2-mica-muskrat-response-blind-geometry-header-v1",
            "status": "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY",
            "candidate_id": "MICA_MUSKRAT",
            "error": f"{type(exc).__name__}: {exc}",
            "response_boundary": {
                "observations_data_rows_read": 0,
                "scientific_name_values_read": False,
                "count_values_read": False,
                "state_values_read": False,
                "model_fits": 0,
                "heldout_scores": 0,
                "authorizes_temporal_opening": False,
                "authorizes_full_response_opening": False,
            },
        }
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": result["status"], "error": result["error"]}))
        return 1

    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "deployment_count": result["geometry"]["deployment_count"],
                "training_deployment_count": result["geometry"]["training_deployment_count"],
                "heldout_deployment_count": result["geometry"]["heldout_deployment_count"],
                "longitude_gap": result["geometry"]["longitude_gap"],
                "training_role_counts": result["roles"]["training_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
