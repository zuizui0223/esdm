#!/usr/bin/env python3
"""Run the frozen response-limited E2 MICA temporal-integrity audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.e2_mica_temporal_integrity import (
    audit_e2_mica_temporal_integrity,
)


ROOT = Path(__file__).resolve().parents[1]
FROZEN_RESPONSE_BLIND = (
    ROOT
    / "docs"
    / "replication"
    / "E2_MICA_RESPONSE_BLIND_GEOMETRY_HEADER_RESULT.json"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = json.loads(FROZEN_RESPONSE_BLIND.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = audit_e2_mica_temporal_integrity(args.archive, receipt)
    except Exception as exc:
        result = {
            "schema_version": 1,
            "result_id": "e2-mica-temporal-integrity-v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "candidate_id": "MICA_MUSKRAT",
            "error": f"{type(exc).__name__}: {exc}",
            "response_boundary": {
                "scientific_name_values_read": False,
                "count_values_read": False,
                "taxon_frequencies_computed": False,
                "focal_event_counts_computed": False,
                "state_frequencies_computed": False,
                "model_fits": 0,
                "heldout_scores": 0,
                "full_response_opened": False,
            },
        }
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": result["status"], "error": result["error"]}))
        return 2

    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "unique_animal_event_count": result["events"][
                    "unique_animal_event_count"
                ],
                "quarantine_event_count": result["quarantine"]["event_count"],
                "quarantine_fraction": result["quarantine"][
                    "fraction_of_unique_animal_events"
                ],
                "stop_reasons": result["decision"]["stop_reasons"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
