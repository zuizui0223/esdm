#!/usr/bin/env python3
"""Run deterministic v0.7k local-repilot audit."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(description="Run v0.7k local-repilot audit.")
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    from esdm.validate.v07k_audit import evaluate_v07k_local_oracle_audit

    args = _parser().parse_args()
    result = evaluate_v07k_local_oracle_audit()
    payload = {
        "schema": "esdm.v07k.local_repilot_audit.v1",
        "status": "COMPLETE",
        "worlds": {
            world: asdict(row)
            for world, row in result.worlds.items()
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
