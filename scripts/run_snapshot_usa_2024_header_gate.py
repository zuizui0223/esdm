#!/usr/bin/env python3
"""Run the frozen response-blind Snapshot USA 2024 metadata/header gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.empirical_snapshot_usa import (
    run_snapshot_usa_metadata_header_gate,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run_snapshot_usa_metadata_header_gate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "response_rows_opened": result["response_rows_opened"],
                "response_values_opened": result["response_values_opened"],
            },
            sort_keys=True,
        )
    )
    valid = {
        "HEADER_AND_DEPLOYMENT_METADATA_QUALIFIED",
        "STOP_PRE_RESPONSE_TRANSPORT",
        "REJECT_PRE_RESPONSE_SCHEMA_OR_GEOMETRY",
    }
    return 0 if result["status"] in valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
