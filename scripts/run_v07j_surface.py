#!/usr/bin/env python3
"""Evaluate the deterministic v0.7j population-shift surface."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(
        description="Evaluate v0.7j population-shift sensitivity."
    )
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    from esdm.validate.v07j_surface import evaluate_v07j_surface

    args = _parser().parse_args()
    result = evaluate_v07j_surface()
    payload = {
        "schema": "esdm.v07j.population_shift_surface.v1",
        "status": "COMPLETE",
        "cell_count": result.cell_count,
        "selected_better_count": result.selected_better_count,
        "selected_better_rate": result.selected_better_rate,
        "mean_ratio": result.mean_ratio,
        "minimum_ratio": result.minimum_ratio,
        "maximum_ratio": result.maximum_ratio,
        "hardest_positive_cell": (
            None
            if result.hardest_positive_cell is None
            else asdict(result.hardest_positive_cell)
        ),
        "easiest_failure_cell": (
            None
            if result.easiest_failure_cell is None
            else asdict(result.easiest_failure_cell)
        ),
        "cells": [asdict(row) for row in result.cells],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
