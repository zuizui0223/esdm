#!/usr/bin/env python3
"""Run one frozen TR1 trait-transfer replicate."""
from __future__ import annotations

import argparse
import hashlib
import json
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
        raise RuntimeError(
            f"TR1 contract blob mismatch: {observed} != {FROZEN_CONTRACT_BLOB_SHA}"
        )


def main() -> int:
    from esdm.validate.tr1_trait_transfer import run_tr1_replicate

    parser = argparse.ArgumentParser()
    parser.add_argument("--world", choices=("positive", "null"), required=True)
    parser.add_argument("--replicate", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    _verify_contract()
    row = run_tr1_replicate(
        world=args.world,
        replicate=args.replicate,
    )
    payload = {
        "schema": "esdm.tr1.shard.v1",
        "status": "COMPLETE",
        "contract_blob_sha": FROZEN_CONTRACT_BLOB_SHA,
        "world": args.world,
        "replicate_index": int(args.replicate),
        "record": row.as_dict(),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
