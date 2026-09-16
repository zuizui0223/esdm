#!/usr/bin/env python3
"""Run the frozen v0.3 in-model SBC study and write an auditable JSON record."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from esdm.model.backend_numpyro import run_numpyro_sbc
from esdm.validate import evaluate_v03_sbc_gate
from esdm.validate.known_truth import make_v03_known_truth_worlds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the frozen generic esdm v0.3 SBC profile.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--replicates",
        type=int,
        default=100,
        help="Prior-predictive SBC replicates; default: 100.",
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=20260917,
        help="Frozen SBC base seed; default: 20260917.",
    )
    parser.add_argument(
        "--num-warmup",
        type=int,
        default=250,
        help="NUTS warmup draws per SBC fit.",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=300,
        help="Retained posterior draws per SBC fit.",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=10,
        help="Rank-histogram bins; default: 10.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/v03_sbc.json"),
        help="JSON artifact path.",
    )
    parser.add_argument("--progress-bar", action="store_true")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    correct = make_v03_known_truth_worlds()[0]
    if correct.name != "correct_effort":
        raise RuntimeError("frozen SBC geometry must be the correct_effort world")

    result = run_numpyro_sbc(
        correct.fitting_model,
        correct.fitting_covariates,
        replicates=args.replicates,
        rng_seed=args.base_seed,
        num_warmup=args.num_warmup,
        num_samples=args.num_samples,
        progress_bar=args.progress_bar,
    )
    decision = evaluate_v03_sbc_gate(result)
    payload = {
        "schema": "esdm.v03_sbc.v1",
        "config": {
            "world": correct.name,
            "target": decision.target,
            "replicates": args.replicates,
            "base_seed": args.base_seed,
            "num_warmup": args.num_warmup,
            "num_samples": args.num_samples,
            "bins": args.bins,
        },
        "ranks": {name: list(values) for name, values in result.ranks.items()},
        "divergences_by_replicate": list(result.divergences_by_replicate),
        "gate": {
            "passed": decision.passed,
            "target": decision.target,
            "histogram": asdict(decision.histogram),
            "mean_divergences": decision.mean_divergences,
            "checks": [asdict(check) for check in decision.checks],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gate": payload["gate"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
