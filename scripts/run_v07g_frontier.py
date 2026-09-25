#!/usr/bin/env python3
"""Run deterministic v0.7g calibration-placement frontier."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(
        description="Evaluate the v0.7g calibration placement frontier."
    )
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    from esdm.validate.v07g_frontier import evaluate_v07g_frontier

    args = _parser().parse_args()
    result = evaluate_v07g_frontier()
    payload = {
        "schema": "esdm.v07g.calibration_frontier.v1",
        "status": "COMPLETE",
        "selection_rule": "minimax occupancy-dynamic target SD proxy",
        "selected": asdict(result.selected),
        "baseline": asdict(result.baseline),
        "selected_to_baseline_worst_sd_ratio": (
            result.selected_to_baseline_worst_sd_ratio
        ),
        "placements_evaluated": len(result.rows),
        "rows": [asdict(row) for row in result.rows],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
