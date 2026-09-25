#!/usr/bin/env python3
"""Export frozen v0.4-R5b activity/state held-out scores to ODSP bundles."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from esdm.transfer import (
    build_v04_r5b_activity_odsp_bundle,
    build_v04_r5b_state_odsp_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    result_path = Path(args.result)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    root = Path(args.out_dir)

    activity = build_v04_r5b_activity_odsp_bundle(payload)
    state = build_v04_r5b_state_odsp_bundle(payload)

    written = {
        "activity": activity.write(root / "activity"),
        "state": state.write(root / "state"),
    }
    print(json.dumps(written, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
