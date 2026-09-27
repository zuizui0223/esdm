#!/usr/bin/env python3
"""Aggregate frozen MAP1 shards and apply the pre-outcome qualification gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from esdm.validate.map1_gate import evaluate_map1_gate, summarize_map1_gains
from esdm.validate.map1_known_truth import make_map1_worlds
from esdm.validate.map1_run import map1_required_fit_plan


REPLICATES = 16
EXPECTED_SHARD_COUNT = 3 * REPLICATES
EXPECTED_FIT_COUNT = 144


def _world_ids():
    return tuple(world.world_id for world in make_map1_worlds())


def _read_shards(root: Path):
    rows = []
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") == "esdm.map1.replicate_result.v1":
            rows.append((path, payload))
    return rows


def aggregate_map1_shards(root: Path):
    expected = {
        (world_id, replicate)
        for world_id in _world_ids()
        for replicate in range(REPLICATES)
    }
    by_identity = {}
    for path, payload in _read_shards(root):
        identity = (str(payload["world_id"]), int(payload["replicate"]))
        if identity in by_identity:
            raise ValueError(f"duplicate MAP1 shard identity {identity!r}")
        by_identity[identity] = (path, payload)

    observed = set(by_identity)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        raise ValueError(f"MAP1 aggregation missing shards: {missing!r}")
    if extra:
        raise ValueError(f"MAP1 aggregation has undeclared shards: {extra!r}")

    worlds = {world.world_id: world for world in make_map1_worlds()}
    gains = defaultdict(list)
    fit_count = 0
    total_divergences = 0

    for identity in sorted(expected):
        _path, payload = by_identity[identity]
        world_id, _replicate = identity
        world = worlds[world_id]

        expected_comparisons = {
            (candidate, reference, holdout)
            for candidate, reference, holdout in (
                *world.expected_positive_comparisons,
                *world.expected_null_comparisons,
            )
        }
        seen_comparisons = set()
        for row in payload["gains"]:
            local = (
                str(row["candidate_model"]),
                str(row["reference_model"]),
                str(row["holdout"]),
            )
            if local in seen_comparisons:
                raise ValueError(f"duplicate MAP1 comparison in {identity!r}: {local!r}")
            seen_comparisons.add(local)
            gains[(world_id, *local)].append(float(row["gain"]))
        if seen_comparisons != expected_comparisons:
            raise ValueError(f"MAP1 shard {identity!r} comparison plan drift")

        expected_fits = set(map1_required_fit_plan(world_id))
        seen_fits = set()
        for row in payload["fits"]:
            key = (str(row["holdout"]), str(row["model_id"]))
            if key in seen_fits:
                raise ValueError(f"duplicate MAP1 fit in {identity!r}: {key!r}")
            seen_fits.add(key)
            divergence = int(row["divergences"])
            if divergence < 0:
                raise ValueError("MAP1 divergences must be non-negative")
            fit_count += 1
            total_divergences += divergence
        if seen_fits != expected_fits:
            raise ValueError(f"MAP1 shard {identity!r} fit plan drift")

    if len(by_identity) != EXPECTED_SHARD_COUNT:
        raise RuntimeError("MAP1 shard-count invariant drift")
    if fit_count != EXPECTED_FIT_COUNT:
        raise RuntimeError(
            f"MAP1 fit-count invariant drift: {fit_count} != {EXPECTED_FIT_COUNT}"
        )

    summaries = []
    for key in sorted(gains):
        world_id, candidate, reference, holdout = key
        summaries.append(
            summarize_map1_gains(
                world_id,
                candidate,
                reference,
                holdout,
                gains[key],
            )
        )
    mean_divergences = total_divergences / fit_count
    decision = evaluate_map1_gate(
        summaries,
        mean_divergences_per_fit=mean_divergences,
    )
    return {
        "schema": "esdm.map1.qualification_result.v1",
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
                "candidate_model": row.candidate_model,
                "reference_model": row.reference_model,
                "holdout": row.holdout,
                "replicates": row.replicates,
                "positive_gain_rate": row.positive_gain_rate,
                "material_gain_rate": row.material_gain_rate,
                "mean_gain": row.mean_gain,
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
        result = aggregate_map1_shards(Path(args.shard_dir))
    except Exception as exc:
        result = {
            "schema": "esdm.map1.qualification_result.v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "scientific_decision": None,
            "error_type": type(exc).__name__,
            "reason": str(exc),
        }
        target.write_text(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True))
        return 2

    target.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "shard_count": result["shard_count"],
        "fit_count": result["fit_count"],
        "claims": result["claims"],
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
