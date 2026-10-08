#!/usr/bin/env python3
"""One-shot, post-outcome camera LocationName QC. Never changes the frozen E5 result.

Four pinned source CSVs are downloaded in memory. Only the LocationName column
is used in statistics, but the files necessarily contain biological event rows.
This is explicitly exploratory and is NOT called response-blind.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Callable
import unicodedata
from urllib.request import Request, urlopen

EXPECTED_CONTRACT_ID = "e5-wildpig-ca-locationname-postoutcome-qc-v1"
EXPECTED_SOURCE_COMMIT = "bc97ff80ec91aba03f58f06629c7e8dfff9eb85d"
SEASONS = ("spring", "summer", "fall", "winter")
REPO = "dwwolfson/gps_cameratrap_activity_comparison"


def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def normalize_locationname(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def fetch_pinned_csv(spec: dict, source_commit: str) -> bytes:
    path = spec["path"]
    if not path.startswith("raw_data/Tejon_CA/Camera/") or ".." in path:
        raise ValueError("source path outside pinned CA camera scope")
    if source_commit != EXPECTED_SOURCE_COMMIT:
        raise ValueError("source commit drift")
    url = (
        "https://raw.githubusercontent.com/"
        + REPO
        + "/"
        + source_commit
        + "/"
        + path
    )
    request = Request(url, headers={"User-Agent": "esdm-e5-postoutcome-locationname-qc/1"})
    expected_size = int(spec["size_bytes"])
    with urlopen(request, timeout=60) as response:
        data = response.read(expected_size + 1)
    if len(data) != expected_size:
        raise ValueError("source file size mismatch")
    if git_blob_sha(data) != spec["git_blob_sha"]:
        raise ValueError("source file Git blob mismatch")
    return data


def extract_label_counts(data: bytes, column: str) -> tuple[Counter, int, int]:
    # csv.reader decodes fields transiently to respect CSV quoting and boundaries.
    # Only the requested LocationName field is retained, and no other field
    # contributes to any calculation or output.
    handle = io.StringIO(data.decode("utf-8-sig"), newline="")
    reader = csv.reader(handle)
    header = next(reader, None)
    if not header or header.count(column) != 1:
        raise ValueError("LocationName header missing or duplicated")
    idx = header.index(column)
    counts: Counter = Counter()
    total_rows = 0
    blank_rows = 0
    for fields in reader:
        if len(fields) != len(header):
            raise ValueError("malformed CSV row shape")
        total_rows += 1
        label = fields[idx]
        if not label.strip() or label.strip().upper() in ("NA", "N/A", "NULL"):
            blank_rows += 1
            continue
        counts[label] += 1
    return counts, total_rows, blank_rows


def run_audit(
    contract: dict,
    fetcher: Callable[[dict, str], bytes] = fetch_pinned_csv,
) -> dict:
    if contract.get("contract_id") != EXPECTED_CONTRACT_ID:
        raise ValueError("unexpected QC contract")
    if contract.get("status") != "FROZEN_EXPLORATORY_POSTOUTCOME_QC_NOT_AUTHORIZED":
        raise ValueError("QC contract not frozen")
    governance = contract["governance"]
    if governance["original_one_shot_rerun_authorized"] is not False:
        raise ValueError("original one-shot boundary changed")
    if governance["focal_model_reestimation_authorized"] is not False:
        raise ValueError("frozen model boundary changed")
    if governance["original_outcome_status_frozen"] != "UNRESOLVED":
        raise ValueError("original outcome reclassified")
    if governance["original_outcome_qc_status_frozen"] != "HOLD_SAMPLE_IDENTITY":
        raise ValueError("original QC hold changed")

    specs = contract["inputs"]
    if len(specs) != 4 or tuple(x["season"] for x in specs) != SEASONS:
        raise ValueError("expected exactly four frozen CA seasonal CSVs")

    counters: dict[str, Counter] = {}
    normalized: dict[str, Counter] = {}
    summaries: dict[str, dict] = {}
    source_commit = contract["provenance"]["source_commit"]
    if source_commit != EXPECTED_SOURCE_COMMIT:
        raise ValueError("unexpected source SHA")

    for spec in specs:
        season = spec["season"]
        data = fetcher(spec, source_commit)
        if len(data) != spec["size_bytes"] or git_blob_sha(data) != spec["git_blob_sha"]:
            raise ValueError("pinned source bytes did not match contract")
        counts, rows, blanks = extract_label_counts(
            data, contract["required_header_field"]
        )
        normalized_counts: Counter = Counter()
        for name, freq in counts.items():
            normalized_counts[normalize_locationname(name)] += freq
        counters[season] = counts
        normalized[season] = normalized_counts
        summaries[season] = {
            "rows_in_original_CSV": rows,
            "blank_or_missing_locationname_rows": blanks,
            "raw_unique_locationname_labels": len(counts),
            "normalized_unique_locationname_labels": len(normalized_counts),
            "raw_singleton_label_count": sum(v == 1 for v in counts.values()),
            "normalized_singleton_label_count": sum(
                v == 1 for v in normalized_counts.values()
            ),
            "public_48_camera_design_exceeded_raw": len(counts) > 48,
            "public_48_camera_design_exceeded_normalized": len(normalized_counts) > 48,
            "full_source_blob_verified": True,
        }

    pairwise = {}
    for i, season_a in enumerate(SEASONS):
        for season_b in SEASONS[i + 1:]:
            pairwise[season_a + "_" + season_b] = {
                "raw_exact_shared_label_count": len(
                    counters[season_a].keys() & counters[season_b].keys()
                ),
                "normalized_shared_label_count": len(
                    normalized[season_a].keys() & normalized[season_b].keys()
                ),
            }
    for season in SEASONS:
        other_raw = set().union(*(
            set(counters[s]) for s in SEASONS if s != season
        ))
        other_norm = set().union(*(
            set(normalized[s]) for s in SEASONS if s != season
        ))
        summaries[season]["raw_labels_shared_with_any_other_season"] = len(
            set(counters[season]) & other_raw
        )
        summaries[season]["raw_labels_unique_to_this_season"] = len(
            set(counters[season]) - other_raw
        )
        summaries[season]["normalized_labels_shared_with_any_other_season"] = len(
            set(normalized[season]) & other_norm
        )
        summaries[season]["normalized_labels_unique_to_this_season"] = len(
            set(normalized[season]) - other_norm
        )

    frozen_summer_valid_count = int(
        contract["provenance"]["already_observed_ca_camera_site_counts"]["summer"]
    )
    if summaries["summer"]["raw_unique_locationname_labels"] < frozen_summer_valid_count:
        status = "STOP_FROZEN_OUTCOME_SOURCE_MISMATCH"
    elif any(
        summaries[s]["normalized_unique_locationname_labels"]
        > contract["provenance"]["public_design_ca_cameras"]
        for s in SEASONS
    ):
        status = "PERSISTENT_RAW_LABEL_GRANULARITY_CONFLICT"
    elif (
        summaries["summer"]["raw_unique_locationname_labels"]
        > contract["provenance"]["public_design_ca_cameras"]
    ):
        status = "TRIM_CASE_LABEL_FORMAT_ONLY_POSSIBLE"
    else:
        status = "NOT_IDENTIFIABLE_FROM_LABEL_COUNTS"

    return {
        "schema_version": 1,
        "programme_id": contract["programme_id"],
        "candidate_id": contract["candidate_id"],
        "route_id": contract["route_id"],
        "status": status,
        "scope": "EXPLORATORY_POSTOUTCOME_LOCATIONNAME_ONLY_DIAGNOSTIC",
        "source": {
            "repo": REPO,
            "pinned_commit": EXPECTED_SOURCE_COMMIT,
            "CA_camera_files_downloaded_and_blob_verified": 4,
        },
        "public_design_camera_count": contract["provenance"]["public_design_ca_cameras"],
        "frozen_original_result": {
            "run_id": contract["provenance"]["reference_outcome_run"],
            "status": "UNRESOLVED",
            "CA_summer_valid_event_locationname_clusters": frozen_summer_valid_count,
            "original_quality_status": "HOLD_SAMPLE_IDENTITY",
        },
        "seasonal_identifier_summaries": summaries,
        "pairwise_identifier_overlaps": pairwise,
        "access_boundary": {
            "downloaded_complete_CSVs_containing_camera_event_rows": 4,
            "only_LocationName_column_used_in_statistics": True,
            "raw_identifiers_in_output": 0,
            "other_biological_columns_used_in_statistics": 0,
            "camera_event_values_or_timestamps_used_in_inference": False,
            "empirical_model_reestimated": False,
            "original_one_shot_rerun": False,
        },
        "decision": {
            "diagnostic_status": status,
            "original_statistical_label_unchanged": "UNRESOLVED",
            "original_quality_hold_remains": True,
            "physical_camera_identity_resolved": False,
            "original_G4_passed": False,
            "original_E5_qualified": False,
            "confirmatory_transfer_claim_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = run_audit(contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
