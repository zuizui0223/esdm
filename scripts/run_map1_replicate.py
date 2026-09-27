#!/usr/bin/env python3
"""Run exactly one frozen MAP1 replicate and serialize evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.validate.map1_run import run_map1_replicate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--replicate", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_map1_replicate(args.world, args.replicate)
    payload = {
        "schema": "esdm.map1.replicate_result.v1",
        "world_id": result.world_id,
        "replicate": result.replicate,
        "gains": [
            {
                "candidate_model": candidate,
                "reference_model": reference,
                "holdout": holdout,
                "gain": gain,
            }
            for (candidate, reference, holdout), gain in sorted(result.gains.items())
        ],
        "fits": [
            {
                "holdout": holdout,
                "model_id": model_id,
                "divergences": divergences,
            }
            for (holdout, model_id), divergences in sorted(result.divergences.items())
        ],
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "world_id": result.world_id,
        "replicate": result.replicate,
        "comparison_count": len(result.gains),
        "fit_count": len(result.divergences),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
