#!/usr/bin/env python3
"""List frozen eSDM sources and their ODSP-transfer eligibility."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import (
    exportable_transfer_sources,
    load_transfer_source_registry,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "ODSP_TRANSFER_SOURCE_REGISTRY_V1.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--exportable-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    sources = load_transfer_source_registry(args.registry)
    if args.exportable_only:
        sources = exportable_transfer_sources(sources)

    if args.json:
        print(
            json.dumps(
                [source.as_dict() for source in sources],
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    width = max(len(source.source_id) for source in sources)
    for source in sources:
        print(
            f"{source.source_id:<{width}}  "
            f"{source.status:<34}  "
            f"{source.reason}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
