#!/usr/bin/env python3
"""Run the frozen v0.3.1 all-parameter SBC component and write auditable JSON."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess

from esdm.model.backend_numpyro import run_numpyro_sbc
from esdm.validate.v031_sbc_fixture import make_v031_sbc_fixture
from esdm.validate.v031_sbc_gate import V031SBCGateConfig, evaluate_v031_sbc_gate


FROZEN_REPLICATES = 100
FROZEN_BASE_SEED = 20260918
FROZEN_WARMUP = 300
FROZEN_SAMPLES = 400
FROZEN_CHAINS = 2
FROZEN_ENVELOPE_SIMULATIONS = 20000
FROZEN_ENVELOPE_SEED = 20260919
FROZEN_EVALUATION_POINTS = 49
FROZEN_ALPHA = 0.05


def build_parser() -> argparse.ArgumentParser:
    description = (
        "Run frozen esdm v0.3.1 all-parameter ESS-aware SBC. "
        f"Profile: replicates={FROZEN_REPLICATES}, seed={FROZEN_BASE_SEED}, "
        f"warmup={FROZEN_WARMUP}, samples={FROZEN_SAMPLES}, chains={FROZEN_CHAINS}, "
        f"envelope_simulations={FROZEN_ENVELOPE_SIMULATIONS}, "
        f"envelope_seed={FROZEN_ENVELOPE_SEED}, evaluation_points={FROZEN_EVALUATION_POINTS}, "
        f"alpha={FROZEN_ALPHA}. Scientific profile is not configurable."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/v031_sbc.json"),
        help="JSON artifact path (default: artifacts/v031_sbc.json).",
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


def _ecdf_payload(ecdf):
    return {
        "passed": ecdf.passed,
        "alpha": ecdf.alpha,
        "simulations": ecdf.simulations,
        "evaluation_grid": list(ecdf.evaluation_grid),
        "critical_max_deviation": ecdf.critical_max_deviation,
        "observed_max_deviation": ecdf.observed_max_deviation,
        "parameter_max_deviation": dict(ecdf.parameter_max_deviation),
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    fixture = make_v031_sbc_fixture()
    result = run_numpyro_sbc(
        fixture.model,
        fixture.covariates,
        replicates=FROZEN_REPLICATES,
        rng_seed=FROZEN_BASE_SEED,
        num_warmup=FROZEN_WARMUP,
        num_samples=FROZEN_SAMPLES,
        num_chains=FROZEN_CHAINS,
        ess_thinning=True,
        progress_bar=args.progress_bar,
    )
    config = V031SBCGateConfig(
        replicates=FROZEN_REPLICATES,
        alpha=FROZEN_ALPHA,
        envelope_simulations=FROZEN_ENVELOPE_SIMULATIONS,
        evaluation_points=FROZEN_EVALUATION_POINTS,
        envelope_seed=FROZEN_ENVELOPE_SEED,
        required_num_chains=FROZEN_CHAINS,
        max_mean_divergences_per_fit=0.10,
    )
    decision = evaluate_v031_sbc_gate(result, config=config)
    payload = {
        "schema": "esdm.v031_sbc.v1",
        "git_sha": _git_sha(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "overall_promotion_status": "NOT_READY",
        "overall_promotion_reason": "Gate F and the remaining mandatory v0.3.1 gates must also pass",
        "config": {
            "replicates": FROZEN_REPLICATES,
            "base_seed": FROZEN_BASE_SEED,
            "num_warmup": FROZEN_WARMUP,
            "num_samples": FROZEN_SAMPLES,
            "num_chains": FROZEN_CHAINS,
            "ess_thinning": True,
            "alpha": FROZEN_ALPHA,
            "envelope_simulations": FROZEN_ENVELOPE_SIMULATIONS,
            "envelope_seed": FROZEN_ENVELOPE_SEED,
            "evaluation_points": FROZEN_EVALUATION_POINTS,
        },
        "ranks": {name: list(values) for name, values in result.ranks.items()},
        "draw_counts_by_site": {
            name: list(values) for name, values in result.draw_counts_by_site.items()
        },
        "effective_sample_sizes_by_site": {
            name: list(values)
            for name, values in result.effective_sample_sizes_by_site.items()
        },
        "divergences_by_replicate": list(result.divergences_by_replicate),
        "gate_e": {
            "passed": decision.passed,
            "mean_divergences": decision.mean_divergences,
            "ecdf": _ecdf_payload(decision.ecdf),
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "observed": check.observed,
                    "criterion": check.criterion,
                }
                for check in decision.checks
            ],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "gate_e_passed": decision.passed,
                "overall": "NOT_READY",
                "git_sha": payload["git_sha"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
