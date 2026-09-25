#!/usr/bin/env python3
"""Run the deterministic fresh-world audit for v0.7l."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.v07l_audit import evaluate_v07l_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    audit = evaluate_v07l_audit()
    payload = {
        "schema": "esdm.v07l.selective_adaptation_audit.v1",
        "status": "COMPLETE",
        **audit.as_dict(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "eligible_cells": sum(row["eligible"] for row in payload["cells"]),
                "selected_worlds": {
                    role: row["cell_id"]
                    for role, row in payload["selected_worlds"].items()
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
