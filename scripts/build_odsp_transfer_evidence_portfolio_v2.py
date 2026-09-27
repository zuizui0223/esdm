#!/usr/bin/env python3
"""Build the complete non-ranking ODSP transfer evidence ledger v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import (
    build_transfer_evidence_portfolio_v2,
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
    portfolio = build_transfer_evidence_portfolio_v2(
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
                "validated_items": len(portfolio["validated_items"]),
                "excluded_sources": len(portfolio["excluded_sources"]),
                "scientific_fail_count": portfolio["coverage_summary"][
                    "scientific_fail_count"
                ],
                "fingerprint": portfolio["fingerprint"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
