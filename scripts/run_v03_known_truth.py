#!/usr/bin/env python3
"""Run the frozen v0.3 known-truth benchmark and write an auditable JSON record."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from esdm.validate.known_truth import (
    evaluate_v03_promotion_gate,
    run_v03_known_truth_benchmark,
)


FROZEN_WORLDS = (
    "correct_effort",
    "wrong_effort_geometry",
    "hidden_driver",
    "suitability_knockout",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the frozen generic esdm v0.3 known-truth benchmark.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--replicates", type=int, default=100)
    parser.add_argument("--base-seed", type=int, default=20260916)
    parser.add_argument("--num-warmup", type=int, default=250)
    parser.add_argument("--num-samples", type=int, default=300)
    parser.add_argument("--credible-mass", type=float, default=0.90)
    parser.add_argument(
        "--worlds",
        default=",".join(FROZEN_WORLDS),
        help="Comma-separated frozen world names.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/v03_known_truth.json"),
    )
    parser.add_argument("--progress-bar", action="store_true")
    return parser


def _decision_payload(summary, selected_worlds):
    if tuple(selected_worlds) != FROZEN_WORLDS:
        return {
            "evaluated": False,
            "reason": "promotion gate requires all four frozen worlds in frozen order",
        }
    decision = evaluate_v03_promotion_gate(summary)
    return {
        "evaluated": True,
        "passed": decision.passed,
        "checks": [asdict(check) for check in decision.checks],
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    worlds = tuple(value.strip() for value in args.worlds.split(",") if value.strip())
    result = run_v03_known_truth_benchmark(
        world_names=worlds,
        replicates=args.replicates,
        base_seed=args.base_seed,
        num_warmup=args.num_warmup,
        num_samples=args.num_samples,
        credible_mass=args.credible_mass,
        progress_bar=args.progress_bar,
    )
    payload = {
        "schema": "esdm.v03_known_truth.v1",
        "config": {
            "worlds": list(worlds),
            "replicates": args.replicates,
            "base_seed": args.base_seed,
            "num_warmup": args.num_warmup,
            "num_samples": args.num_samples,
            "credible_mass": args.credible_mass,
        },
        "summary": {name: asdict(row) for name, row in result.summary.items()},
        "replicates": [asdict(row) for row in result.replicates],
        "promotion_gate": _decision_payload(result.summary, worlds),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "promotion_gate": payload["promotion_gate"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
