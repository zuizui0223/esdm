#!/usr/bin/env python3
"""Build the normalized non-ranking ODSP transfer evidence portfolio."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import (
    build_transfer_evidence_portfolio,
    load_transfer_source_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        default="ODSP_TRANSFER_SOURCE_REGISTRY_V1.json",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    registry_path = Path(args.registry)
    root = registry_path.resolve().parent
    sources = load_transfer_source_registry(registry_path)
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    portfolio = build_transfer_evidence_portfolio(
        repository_root=root,
        registry_id=registry_payload["registry_id"],
        sources=sources,
    ).as_dict()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(portfolio, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "items": len(portfolio["items"]),
                "parallel_families": len(portfolio["parallel_families"]),
                "fingerprint": portfolio["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
