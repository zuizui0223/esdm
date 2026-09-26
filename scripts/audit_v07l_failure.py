#!/usr/bin/env python3
"""Audit the frozen v0.7l FAIL without rerunning simulation or MCMC."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.v07l_failure_audit import audit_v07l_failure


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    frozen = json.loads(args.result.read_text(encoding="utf-8"))
    audit = audit_v07l_failure(frozen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "threshold_only_rescue_possible": audit[
                    "threshold_only_rescue_possible"
                ],
                "any_scalar_threshold_recovery_guardrails_pass": audit[
                    "any_scalar_threshold_recovery_guardrails_pass"
                ],
                "best_balanced_accuracy_threshold": audit[
                    "best_balanced_accuracy_scalar_threshold"
                ]["trigger_threshold"],
                "oracle_recovery_guardrails_pass": audit[
                    "oracle_material_headroom"
                ]["recovery_guardrails_pass"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
