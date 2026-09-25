#!/usr/bin/env python3
"""Evaluate deterministic v0.7h expected-record matched control."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(description="Run deterministic v0.7h control.")
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    from esdm.validate.v07h_diagnostic import evaluate_v07h_comparison

    args = _parser().parse_args()
    result = evaluate_v07h_comparison()
    payload = {
        "schema": "esdm.v07h.expected_record_match.v1",
        "status": "COMPLETE",
        **asdict(result),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
