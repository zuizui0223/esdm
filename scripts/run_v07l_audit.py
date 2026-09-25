#!/usr/bin/env python3
"""Run the deterministic v0.7l fresh-cell audit."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(description="Run v0.7l fresh-cell audit.")
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    from esdm.validate.v07l_audit import evaluate_v07l_audit

    args = _parser().parse_args()
    audit = evaluate_v07l_audit()
    payload = {
        "schema": "esdm.v07l.pilot_gated_adaptation_audit.v1",
        "status": "COMPLETE",
        "trigger_ratio": audit.trigger_ratio,
        "eligible_fresh_cells": audit.eligible_fresh_cells,
        "high_headroom": [asdict(row) for row in audit.high_headroom],
        "low_headroom": [asdict(row) for row in audit.low_headroom],
        "all_fresh_cells": [asdict(row) for row in audit.all_fresh_cells],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
