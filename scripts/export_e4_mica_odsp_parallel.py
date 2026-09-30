#!/usr/bin/env python3
"""Export the frozen E4 MICA empirical result as two parallel ODSP bundles."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import (
    build_e4_mica_activity_odsp_bundle,
    build_e4_mica_state_odsp_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    activity = build_e4_mica_activity_odsp_bundle(result)
    state = build_e4_mica_state_odsp_bundle(result)

    payload = {
        "activity": activity.write(args.out_dir / "activity"),
        "state": state.write(args.out_dir / "state"),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
