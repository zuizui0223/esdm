#!/usr/bin/env python3
"""Aggregate the frozen TR1 trait-transfer known-truth programme."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "TR1_TRAIT_TRANSFER_CONTRACT_V1.json"
FROZEN_CONTRACT_BLOB_SHA = "91114caab4713ae48ac2976a56935abfdbbf51a2"


def _git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload
    ).hexdigest()


def _verify_contract() -> None:
    observed = _git_blob_sha1(CONTRACT_PATH.read_bytes())
    if observed != FROZEN_CONTRACT_BLOB_SHA:
        raise RuntimeError("TR1 contract blob mismatch")


def main() -> int:
    from esdm.validate.tr1_gate import evaluate_tr1_gate
    from esdm.validate.tr1_trait_transfer import (
        TR1Replicate,
        seed_for,
        summarize_tr1_world,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    _verify_contract()
    paths = sorted(Path(args.shard_dir).rglob("*.json"))
    if len(paths) != 64:
        raise RuntimeError(f"TR1 requires exactly 64 shards, found {len(paths)}")

    keyed = {}
    for path in paths:
        shard = json.loads(path.read_text(encoding="utf-8"))
        if shard.get("schema") != "esdm.tr1.shard.v1":
            raise RuntimeError(f"unexpected TR1 shard schema: {path}")
        if shard.get("status") != "COMPLETE":
            raise RuntimeError(f"TR1 shard not complete: {path}")
        if shard.get("contract_blob_sha") != FROZEN_CONTRACT_BLOB_SHA:
            raise RuntimeError("TR1 shard contract hash mismatch")
        world = str(shard["world"])
        replicate = int(shard["replicate_index"])
        key = (world, replicate)
        if key in keyed:
            raise RuntimeError(f"duplicate TR1 shard {key}")
        row = TR1Replicate(**{
            name: value
            for name, value in shard["record"].items()
            if name != "trait_gain"
        })
        if row.seed != seed_for(world, replicate):
            raise RuntimeError(f"TR1 seed mismatch for {key}")
        for value in (
            row.environment_only_heldout_log_score,
            row.environment_trait_heldout_log_score,
            row.fitted_trait_coefficient,
            row.trait_gain,
        ):
            if not math.isfinite(float(value)):
                raise RuntimeError(f"non-finite TR1 value for {key}")
        keyed[key] = row

    expected = {
        (world, replicate)
        for world in ("positive", "null")
        for replicate in range(32)
    }
    if set(keyed) != expected:
        raise RuntimeError("TR1 shard coverage is incomplete")

    positive_rows = tuple(keyed[("positive", index)] for index in range(32))
    null_rows = tuple(keyed[("null", index)] for index in range(32))
    positive = summarize_tr1_world(positive_rows)
    null = summarize_tr1_world(null_rows)
    decision = evaluate_tr1_gate(positive, null)

    result = {
        "schema": "esdm.tr1.trait_transfer.v1",
        "status": "PASS" if decision.passed else "FAIL",
        "contract_id": "esdm-tr1-trait-transfer-known-truth-v1",
        "contract_blob_sha": FROZEN_CONTRACT_BLOB_SHA,
        "information_filtration": [
            {
                "name": "environment_only",
                "information": ["environment"],
                "score_field": "environment_only_heldout_log_score",
            },
            {
                "name": "environment_traits",
                "information": ["environment", "traits"],
                "score_field": "environment_trait_heldout_log_score",
            },
        ],
        "score_contract": {
            "kind": "log",
            "name": "mean_heldout_log_predictive_density",
            "unit": "nats_per_heldout_context",
            "orientation": "higher_is_better",
        },
        "positive_summary": positive.as_dict(),
        "null_summary": null.as_dict(),
        "gate": {
            "passed": decision.passed,
            "checks": [
                {
                    "name": row.name,
                    "passed": row.passed,
                    "observed": row.observed,
                    "criterion": row.criterion,
                }
                for row in decision.checks
            ],
        },
        "positive_replicates": [row.as_dict() for row in positive_rows],
        "null_replicates": [row.as_dict() for row in null_rows],
        "claim_boundary": {
            "empirical_trait_importance": False,
            "phylogenetic_effect": False,
            "causal_trait_effect": False,
            "movement_information": False,
            "interaction_information": False,
            "n4_action": False,
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
