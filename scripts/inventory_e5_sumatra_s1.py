#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

README_RE = re.compile(r"(^|/)(readme|read_me)(\.[a-z0-9]+)?$", re.I)
TEXT_SUFFIXES = {".md", ".txt", ".rtf"}
DATA_SUFFIXES = {
    ".csv", ".tsv", ".xlsx", ".xls", ".rdata", ".rds", ".json",
    ".sqlite", ".db", ".parquet", ".sav", ".dta",
}

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def inventory(path: Path) -> dict:
    raw = path.read_bytes()
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if not n.endswith("/"))
        opened = []
        readmes = []
        for name in names:
            p = PurePosixPath(name)
            if README_RE.search(p.as_posix()):
                if p.suffix.lower() not in TEXT_SUFFIXES:
                    raise ValueError("README-like member has unexpected suffix")
                data = z.read(name)
                text = data.decode("utf-8-sig", errors="strict")
                opened.append(name)
                readmes.append({
                    "member": name,
                    "sha256": _sha256(data),
                    "line_count": len(text.splitlines()),
                    "text": text,
                })
        data_like = [
            n for n in names
            if PurePosixPath(n).suffix.lower() in DATA_SUFFIXES
        ]
    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "sumatra_mesopredator_paired_2014_2015",
        "inventory_id": "e5-sumatra-mesopredator-s1-inventory-result-v1",
        "status": "E5_RESPONSE_BLIND_PACKAGE_INVENTORY",
        "archive": {
            "sha256": _sha256(raw),
            "member_count": len(names),
            "member_names": names,
        },
        "response_boundary": {
            "readme_members_opened": opened,
            "non_readme_members_opened": [],
            "data_rows_read": 0,
            "response_rows_read": 0,
            "focal_response_opened": False,
        },
        "readmes": readmes,
        "data_like_members_present_but_unopened": data_like,
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "separate_metadata_child_contract_required": True,
        },
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    value = inventory(args.archive)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
