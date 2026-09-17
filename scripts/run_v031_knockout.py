#!/usr/bin/env python3
"""Run the frozen v0.3.1 Gate C neutral-suitability knockout benchmark."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess


FROZEN_REPLICATES = 100
FROZEN_BASE_SEED = 20260920
FROZEN_WARMUP = 250
FROZEN_SAMPLES = 300
FROZEN_CHAINS = 2
FROZEN_CREDIBLE_MASS = 0.90


def _parser() -> argparse.ArgumentParser:
    description = (
        "Run frozen esdm v0.3.1 Gate C neutral-slope knockout. "
        f"Profile: replicates={FROZEN_REPLICATES}, seed={FROZEN_BASE_SEED}, "
        f"warmup={FROZEN_WARMUP}, samples={FROZEN_SAMPLES}, chains={FROZEN_CHAINS}, "
        f"credible_mass={FROZEN_CREDIBLE_MASS:.2f}. Scientific profile is not configurable."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/v031_knockout.json"),
        help="JSON artifact path (default: artifacts/v031_knockout.json)",
    )
    parser.add_argument(
        "--progress-bar",
        action="store_true",
        help="show NumPyro progress bars; does not change the frozen scientific profile",
    )
    return parser


def _git_sha() -> str:
    from_env = os.environ.get("GITHUB_SHA") or os.environ.get("ESDM_GIT_SHA")
    if from_env:
        return from_env
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    args = _parser().parse_args()
    from esdm.validate.v031_knockout import (
        evaluate_v031_knockout_gate,
        make_v031_neutral_knockout_world,
        run_v031_knockout_benchmark,
    )

    world = make_v031_neutral_knockout_world()
    result = run_v031_knockout_benchmark(
        replicates=FROZEN_REPLICATES,
        base_seed=FROZEN_BASE_SEED,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        credible_mass=FROZEN_CREDIBLE_MASS,
        progress_bar=bool(args.progress_bar),
    )
    decision = evaluate_v031_knockout_gate(result.summary)
    payload = {
        "schema": "esdm.v031.gate_c.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "promotion_status": "NOT_READY",
        "promotion_note": "Gate C is one mandatory v0.3.1 gate; overall promotion requires A-F.",
        "frozen_profile": {
            "replicates": FROZEN_REPLICATES,
            "base_seed": FROZEN_BASE_SEED,
            "num_warmup": FROZEN_WARMUP,
            "num_samples": FROZEN_SAMPLES,
            "num_chains": FROZEN_CHAINS,
            "credible_mass": FROZEN_CREDIBLE_MASS,
        },
        "world_contract": {
            "target_parameter": world.target_parameter,
            "truth": world.truth,
            "generating_parameters": {
                species: dict(values) for species, values in world.generating_theta.items()
            },
            "knockout_semantics": "preserve intercept; neutralize environmental slope only",
        },
        "replicates": [
            asdict(row)
            | {
                "covers_zero": row.covers_zero,
                "nonzero": row.nonzero,
            }
            for row in result.replicates
        ],
        "summary": asdict(result.summary),
        "gate_c": {
            "passed": decision.passed,
            "checks": [asdict(check) for check in decision.checks],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "gate_c_passed": decision.passed,
                "promotion_status": payload["promotion_status"],
                "git_sha": payload["git_sha"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
