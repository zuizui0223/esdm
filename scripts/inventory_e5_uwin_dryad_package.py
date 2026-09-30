#!/usr/bin/env python3
"""Response-blind inventory of the public UWIN/Gallo Dryad package.

Only ZIP member names and README-like text members may be opened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile


README_RE = re.compile(r"(^|/)(readme|read_me)(\.[a-z0-9]+)?$", re.I)
FORBIDDEN_SUFFIXES = {
    ".csv", ".tsv", ".xlsx", ".xls", ".rdata", ".rds", ".parquet",
    ".feather", ".json", ".sqlite", ".db",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(archive_path: Path) -> dict:
    raw = archive_path.read_bytes()
    archive_sha = _sha256(raw)
    archive_md5 = hashlib.md5(raw).hexdigest()

    with zipfile.ZipFile(archive_path) as archive:
        names = sorted(name for name in archive.namelist() if not name.endswith("/"))
        readmes = [
            name for name in names
            if README_RE.search(PurePosixPath(name).as_posix())
        ]
        opened = []
        readme_records = []
        for name in readmes:
            suffix = PurePosixPath(name).suffix.lower()
            if suffix in FORBIDDEN_SUFFIXES:
                raise ValueError("README candidate has forbidden data suffix")
            data = archive.read(name)
            text = data.decode("utf-8-sig", errors="strict")
            opened.append(name)
            readme_records.append({
                "member": name,
                "sha256": _sha256(data),
                "line_count": len(text.splitlines()),
                "text": text,
            })

    data_like = [
        name for name in names
        if PurePosixPath(name).suffix.lower() in FORBIDDEN_SUFFIXES
    ]

    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": "uwin_gallo_10city_2017_2018",
        "inventory_id": "e5-uwin-dryad-package-response-blind-inventory-result-v1",
        "status": "E5_RESPONSE_BLIND_PACKAGE_INVENTORY",
        "archive": {
            "sha256": archive_sha,
            "md5": archive_md5,
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
        "readmes": readme_records,
        "data_like_members_present_but_unopened": data_like,
        "decision": {
            "candidate_qualified": False,
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "non_readme_metadata_member_opening_authorized": False,
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
