#!/usr/bin/env python3
"""Export a successful TR1 trait-transfer result as an ODSP bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import build_tr1_trait_odsp_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    bundle = build_tr1_trait_odsp_bundle(result)
    written = bundle.write(Path(args.out_dir))
    print(json.dumps(written, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
