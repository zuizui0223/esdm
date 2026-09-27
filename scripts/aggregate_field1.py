#!/usr/bin/env python3
"""Aggregate all frozen FIELD1 shards and apply the pre-outcome qualification gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

from esdm.validate.field1_gate import (
    evaluate_field1_gate,
    summarize_field1_gains,
)
from esdm.validate.field1_known_truth import (
    make_field1_fixture,
    make_field1_mean_covariance_factorial,
    make_field1_primary_worlds,
    matched_barrier_distance_strata,
)
from esdm.validate.field1_run import field1_required_fit_plan


REPLICATES = 16
EXPECTED_SHARD_COUNT = 9 * REPLICATES
EXPECTED_FIT_COUNT = 704


def _world_ids():
    return tuple(
        world.world_id
        for world in (
            *make_field1_primary_worlds(),
            *make_field1_mean_covariance_factorial(),
        )
    )


def _parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser


def _read_shards(root: Path):
    rows = []
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != "esdm.field1.replicate_result.v1":
            continue
        rows.append((path, payload))
    return rows


def aggregate_field1_shards(root: Path):
    rows = _read_shards(root)
    expected = {
        (world_id, replicate)
        for world_id in _world_ids()
        for replicate in range(REPLICATES)
    }
    by_identity = {}
    for path, payload in rows:
        identity = (
            str(payload["world_id"]),
            int(payload["replicate"]),
        )
        if identity in by_identity:
            raise ValueError(
                f"duplicate FIELD1 shard identity {identity!r}: "
                f"{by_identity[identity][0]} and {path}"
            )
        by_identity[identity] = (path, payload)

    observed = set(by_identity)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing:
        raise ValueError(f"FIELD1 aggregation missing shards: {missing!r}")
    if extra:
        raise ValueError(f"FIELD1 aggregation has undeclared shards: {extra!r}")

    world_map = {
        world.world_id: world
        for world in (
            *make_field1_primary_worlds(),
            *make_field1_mean_covariance_factorial(),
        )
    }

    gains = defaultdict(list)
    fit_count = 0
    total_divergences = 0
    for identity in sorted(expected):
        _path, payload = by_identity[identity]
        world_id, _replicate = identity
        world = world_map[world_id]

        expected_comparisons = {
            (str(candidate), str(reference), str(holdout))
            for candidate, reference, holdout in (
                *world.expected_positive_comparisons,
                *world.expected_null_comparisons,
            )
        }
        seen_comparisons = set()
        for row in payload["gains"]:
            local_key = (
                str(row["candidate_model"]),
                str(row["reference_model"]),
                str(row["holdout"]),
            )
            if local_key in seen_comparisons:
                raise ValueError(
                    f"duplicate comparison inside FIELD1 shard {identity!r}: "
                    f"{local_key!r}"
                )
            seen_comparisons.add(local_key)
            key = (world_id, *local_key)
            gains[key].append(float(row["gain"]))
        if seen_comparisons != expected_comparisons:
            missing_local = sorted(expected_comparisons - seen_comparisons)
            extra_local = sorted(seen_comparisons - expected_comparisons)
            raise ValueError(
                f"FIELD1 shard {identity!r} comparison plan drift: "
                f"missing={missing_local!r}, extra={extra_local!r}"
            )

        expected_fits = set(field1_required_fit_plan(world_id))
        seen_fits = set()
        for fit in payload["fits"]:
            fit_key = (str(fit["holdout"]), str(fit["model_id"]))
            if fit_key in seen_fits:
                raise ValueError(
                    f"duplicate fit inside FIELD1 shard {identity!r}: {fit_key!r}"
                )
            seen_fits.add(fit_key)
            divergence = int(fit["divergences"])
            if divergence < 0:
                raise ValueError("FIELD1 divergences must be non-negative")
            fit_count += 1
            total_divergences += divergence
        if seen_fits != expected_fits:
            missing_fits = sorted(expected_fits - seen_fits)
            extra_fits = sorted(seen_fits - expected_fits)
            raise ValueError(
                f"FIELD1 shard {identity!r} fit plan drift: "
                f"missing={missing_fits!r}, extra={extra_fits!r}"
            )

    summaries = []
    for key in sorted(gains):
        world_id, candidate, reference, holdout = key
        summaries.append(
            summarize_field1_gains(
                world_id,
                candidate,
                reference,
                holdout,
                gains[key],
            )
        )

    fixture = make_field1_fixture()
    k6_strata = matched_barrier_distance_strata(fixture)
    k6_pass = bool(k6_strata)
    mean_divergences = (
        total_divergences / fit_count if fit_count else math.inf
    )
    if len(by_identity) != EXPECTED_SHARD_COUNT:
        raise RuntimeError(
            f"FIELD1 shard-count invariant drift: {len(by_identity)} "
            f"!= {EXPECTED_SHARD_COUNT}"
        )
    if fit_count != EXPECTED_FIT_COUNT:
        raise RuntimeError(
            f"FIELD1 fit-count invariant drift: {fit_count} "
            f"!= {EXPECTED_FIT_COUNT}"
        )

    decision = evaluate_field1_gate(
        summaries,
        k6_distance_match_passed=k6_pass,
        mean_divergences_per_fit=mean_divergences,
    )

    return {
        "schema": "esdm.field1.qualification_result.v1",
        "status": "PASS" if decision.passed else "FAIL",
        "replicates_per_world": REPLICATES,
        "world_ids": list(_world_ids()),
        "shard_count": len(by_identity),
        "fit_count": fit_count,
        "total_divergences": total_divergences,
        "mean_divergences_per_fit": mean_divergences,
        "k6_distance_match_passed": k6_pass,
        "k6_matched_distance_strata": {
            str(distance): dict(counts)
            for distance, counts in k6_strata.items()
        },
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
    args = _parser().parse_args()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = aggregate_field1_shards(Path(args.shard_dir))
    except Exception as exc:
        result = {
            "schema": "esdm.field1.qualification_result.v1",
            "status": "INFRASTRUCTURE_BLOCKED",
            "scientific_decision": None,
            "error_type": type(exc).__name__,
            "reason": str(exc),
        }
        target.write_text(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": result["status"],
            "error_type": result["error_type"],
            "reason": result["reason"],
        }, sort_keys=True))
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
