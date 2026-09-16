#!/usr/bin/env python3
"""Run the frozen v0.3.1 all-parameter SBC component and write auditable JSON."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from esdm.model.backend_numpyro import run_numpyro_sbc
from esdm.validate.v031_sbc_fixture import make_v031_sbc_fixture
from esdm.validate.v031_sbc_gate import V031SBCGateConfig, evaluate_v031_sbc_gate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run frozen esdm v0.3.1 all-parameter ESS-aware SBC.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--replicates", type=int, default=100, help="SBC replicates; default: 100.")
    parser.add_argument("--base-seed", type=int, default=20260918, help="SBC base seed; default: 20260918.")
    parser.add_argument("--num-warmup", type=int, default=300, help="Warmup draws per chain; default: 300.")
    parser.add_argument("--num-samples", type=int, default=400, help="Retained draws per chain before ESS thinning; default: 400.")
    parser.add_argument("--num-chains", type=int, default=2, help="Sequential MCMC chains; default: 2.")
    parser.add_argument("--envelope-simulations", type=int, default=20000, help="Null-envelope Monte Carlo simulations; default: 20000.")
    parser.add_argument("--envelope-seed", type=int, default=20260919, help="Null-envelope seed; default: 20260919.")
    parser.add_argument("--evaluation-points", type=int, default=49, help="ECDF evaluation points; default: 49.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Familywise ECDF level.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/v031_sbc.json"),
        help="JSON artifact path.",
    )
    parser.add_argument("--progress-bar", action="store_true")
    return parser


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
        replicates=args.replicates,
        rng_seed=args.base_seed,
        num_warmup=args.num_warmup,
        num_samples=args.num_samples,
        num_chains=args.num_chains,
        ess_thinning=True,
        progress_bar=args.progress_bar,
    )
    config = V031SBCGateConfig(
        replicates=args.replicates,
        alpha=args.alpha,
        envelope_simulations=args.envelope_simulations,
        evaluation_points=args.evaluation_points,
        envelope_seed=args.envelope_seed,
        required_num_chains=args.num_chains,
        max_mean_divergences_per_fit=0.10,
    )
    decision = evaluate_v031_sbc_gate(result, config=config)
    payload = {
        "schema": "esdm.v031_sbc.v1",
        "git_sha": os.environ.get("GITHUB_SHA") or os.environ.get("ESDM_GIT_SHA"),
        "overall_promotion_status": "NOT_READY",
        "overall_promotion_reason": "Gate F semi-synthetic real geometry remains mandatory",
        "config": {
            "replicates": args.replicates,
            "base_seed": args.base_seed,
            "num_warmup": args.num_warmup,
            "num_samples": args.num_samples,
            "num_chains": args.num_chains,
            "ess_thinning": True,
            "alpha": args.alpha,
            "envelope_simulations": args.envelope_simulations,
            "envelope_seed": args.envelope_seed,
            "evaluation_points": args.evaluation_points,
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
    print(json.dumps({"output": str(args.output), "gate_e_passed": decision.passed, "overall": "NOT_READY"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
