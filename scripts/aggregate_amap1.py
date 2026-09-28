#!/usr/bin/env python3
"""Aggregate frozen AMAP1 shards and apply the pre-outcome low-regret gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from esdm.validate.amap1_gate import (
    evaluate_amap1_gate,
    summarize_amap1_world,
)
from esdm.validate.amap1_known_truth import make_amap1_worlds
from esdm.validate.amap1_run import amap1_required_fit_plan


REPLICATES = 16
EXPECTED_SHARD_COUNT = 9 * REPLICATES
EXPECTED_FIT_COUNT = 384


def _world_ids():
    return tuple(world.world_id for world in make_amap1_worlds())


def _read_shards(root: Path):
    rows = []
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") == "esdm.amap1.replicate_result.v1":
            rows.append((path, payload))
    return rows


def aggregate_amap1_shards(root: Path):
    expected = {
        (world_id, replicate)
        for world_id in _world_ids()
        for replicate in range(REPLICATES)
    }
    by_identity = {}
    for path, payload in _read_shards(root):
        identity = (
            str(payload["world_id"]),
            int(payload["replicate"]),
        )
        if identity in by_identity:
            raise ValueError(
                f"duplicate AMAP1 shard identity {identity!r}"
            )
        by_identity[identity] = (path, payload)

    observed = set(by_identity)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        raise ValueError(f"AMAP1 aggregation missing shards: {missing!r}")
    if extra:
        raise ValueError(
            f"AMAP1 aggregation has undeclared shards: {extra!r}"
        )

    worlds = {world.world_id: world for world in make_amap1_worlds()}
    regrets = defaultdict(list)
    detectability = defaultdict(list)
    fit_count = 0
    total_divergences = 0

    for identity in sorted(expected):
        _path, payload = by_identity[identity]
        world_id, _replicate = identity
        world = worlds[world_id]

        regret = float(payload["regret"])
        regrets[world_id].append(regret)

        raw_detectability = payload.get("detectability_gain")
        if world.detectability_reference is None:
            if raw_detectability is not None:
                raise ValueError(
                    f"AMAP1 T0 shard {identity!r} carries detectability outcome"
                )
        else:
            if raw_detectability is None:
                raise ValueError(
                    f"AMAP1 field-positive shard {identity!r} lacks detectability"
                )
            detectability[world_id].append(float(raw_detectability))

        expected_fits = set(amap1_required_fit_plan(world_id))
        seen_fits = set()
        for row in payload["fits"]:
            model_id = str(row["model_id"])
            if model_id in seen_fits:
                raise ValueError(
                    f"duplicate AMAP1 fit in {identity!r}: {model_id!r}"
                )
            seen_fits.add(model_id)
            divergence = int(row["divergences"])
            if divergence < 0:
                raise ValueError("AMAP1 divergences must be non-negative")
            fit_count += 1
            total_divergences += divergence

        if seen_fits != expected_fits:
            missing_fits = sorted(expected_fits - seen_fits)
            extra_fits = sorted(seen_fits - expected_fits)
            raise ValueError(
                f"AMAP1 shard {identity!r} fit plan drift: "
                f"missing={missing_fits!r}, extra={extra_fits!r}"
            )

    if len(by_identity) != EXPECTED_SHARD_COUNT:
        raise RuntimeError(
            f"AMAP1 shard-count invariant drift: "
            f"{len(by_identity)} != {EXPECTED_SHARD_COUNT}"
        )
    if fit_count != EXPECTED_FIT_COUNT:
        raise RuntimeError(
            f"AMAP1 fit-count invariant drift: "
            f"{fit_count} != {EXPECTED_FIT_COUNT}"
        )

    summaries = []
    for world in make_amap1_worlds():
        summaries.append(
            summarize_amap1_world(
                world.world_id,
                regrets[world.world_id],
                detectability_gains=(
                    None
                    if world.detectability_reference is None
                    else detectability[world.world_id]
                ),
            )
        )

    mean_divergences = total_divergences / fit_count
    decision = evaluate_amap1_gate(
        summaries,
        mean_divergences_per_fit=mean_divergences,
    )
    return {
        "schema": "esdm.amap1.qualification_result.v1",
        "status": "PASS" if decision.passed else "FAIL",
        "replicates_per_world": REPLICATES,
        "world_ids": list(_world_ids()),
        "shard_count": len(by_identity),
        "fit_count": fit_count,
        "total_divergences": total_divergences,
        "mean_divergences_per_fit": mean_divergences,
        "summaries": [
            {
                "world_id": row.world_id,
                "geometry_id": row.geometry_id,
                "truth_id": row.truth_id,
                "oracle_model_id": row.oracle_model_id,
                "replicates": row.replicates,
                "material_regret_rate": row.material_regret_rate,
                "mean_regret": row.mean_regret,
                "detectability_positive_rate": row.detectability_positive_rate,
                "detectability_mean_gain": row.detectability_mean_gain,
            }
            for row in summaries
        ],
        "claims": dict(decision.claims),
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
                "observed": check.observed,
                "criterion": check.criterion,
            }
            for check in decision.checks
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = aggregate_amap1_shards(Path(args.shard_dir))
    except Exception as exc:
        result = {
            "schema": "esdm.amap1.qualification_result.v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "scientific_decision": None,
            "error_type": type(exc).__name__,
            "reason": str(exc),
        }
        target.write_text(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True))
        return 2

    target.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "shard_count": result["shard_count"],
                "fit_count": result["fit_count"],
                "claims": result["claims"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
