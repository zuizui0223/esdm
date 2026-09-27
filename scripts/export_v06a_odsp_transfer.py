#!/usr/bin/env python3
"""Export a completed eSDM v0.6a result as an ODSP transfer bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import build_v06a_accessibility_odsp_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result_path = Path(args.result)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    bundle = build_v06a_accessibility_odsp_bundle(payload)
    written = bundle.write(Path(args.out_dir))
    print(json.dumps(written, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
