#!/usr/bin/env python3
"""Reconstruct safe source-dataset aggregates from the frozen NeoBat plant ZIP.

Python 3.10+ standard library only. No GBIF download requests are submitted.
The existing ZIP is read locally; only dataset metadata are fetched from GBIF.
Frozen repository receipts are read from --input-dir or fetched at an immutable
commit and verified using their Git blob hashes. No occurrence rows, coordinates,
occurrence identifiers, or cell identifiers are written.

Example from the repository root:
  python scripts/neobat_gbif_cr_pa_source_registry.py \
    --archive /path/to/0001157-261118162104854.zip \
    --input-dir docs/replication/neobat --output-dir build/neobat/source_registry

The original 255-name source download must be distinguished from the fixed
106-name focal roster and from later cell/raster/model-specific retained inputs.
This script reconstructs source membership, not scientific source independence.
"""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
from urllib.request import Request, urlopen
import zipfile


REPOSITORY = "zuizui0223/esdm"
COMMIT = "d65817fcb3c39060ed544261c291d76a198299c6"
INPUT_PATH = "docs/replication/neobat"
INPUT_BLOBS = {
    "v2_106plant_reference_input_gate.json": "3e1aead01ec672ce73d7db05ba9ef222ee21e468",
    "plant_search_preflight.json": "7c810fea62fd6e0e4bbe215faccad6900e858055",
    "gbif_archive_header_preflight.json": "d213a8941815f9ccc8f1d99343cacb233f9732dd",
    "plant_106x17_global_source_embargo_compact.json": "bbe9ff61542af3975fa5917e1c84972f997a4220",
    "gbif_full_source_qc_summary.json": "c848edea26bf070de22d3fb59e1bc76c072cc02c",
}
DOWNLOAD_KEY = "0001157-261118162104854"
DOI = "10.15468/dl.xwc5zf"
ARCHIVE_SHA = "4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b"
ARCHIVE_SIZE = 39741309
EXPECTED_ROWS = 367988
EXPECTED_DATASETS = 1202
ROSTER_SHA = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
METADATA_URL = f"https://api.gbif.org/v1/occurrence/download/{DOWNLOAD_KEY}/datasets"
ARCHIVE_URL = f"https://api.gbif.org/v1/occurrence/download/request/{DOWNLOAD_KEY}.zip"
FOCUS_COUNTRIES = ("CR", "PA")


def require(condition, message):
    """Validation remains active with python -O."""
    if not condition:
        raise ValueError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_bytes(url, limit=4 * 1024 * 1024):
    request = Request(url, headers={"User-Agent": "esdm-NeoBat-source-registry/1.0"})
    with urlopen(request, timeout=60) as response:
        require(response.status == 200, f"Unexpected HTTP status for {url}")
        data = response.read(limit + 1)
    require(len(data) <= limit, f"Metadata exceeds byte limit: {url}")
    return data


def load_inputs(input_dir):
    documents = {}
    provenance = []
    for name, expected_blob in INPUT_BLOBS.items():
        path = f"{INPUT_PATH}/{name}"
        raw_url = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/{path}"
        data = (input_dir / name).read_bytes() if input_dir else fetch_bytes(raw_url)
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(blob == expected_blob, f"Frozen input Git blob mismatch: {name}")
        documents[name] = json.loads(data)
        provenance.append({
            "path": path, "git_blob_sha1": blob,
            "content_sha256": hashlib.sha256(data).hexdigest(),
            "source_url": f"https://github.com/{REPOSITORY}/blob/{COMMIT}/{path}",
            "raw_source_url": raw_url,
        })
    return documents, provenance


def validate_inputs(documents):
    roster_receipt = documents["v2_106plant_reference_input_gate.json"]
    names = roster_receipt["v2_fixed_plant_names"]
    require(len(names) == 106 and names == sorted(set(names)), "Frozen106 names changed")
    require(hashlib.sha256(("\n".join(names) + "\n").encode()).hexdigest() == ROSTER_SHA,
            "Frozen106 name hash mismatch")
    require(roster_receipt["v2_fixed_plant_universe_sha256"] == ROSTER_SHA,
            "Frozen106 receipt hash mismatch")
    accepted = {}
    for row in documents["plant_search_preflight.json"]["plants"]:
        if row.get("status") != "GBIF_PLANT_COUNTS_ONLY":
            continue
        key = str(row["match"].get("acceptedUsageKey") or row["match"]["usageKey"])
        require(key not in accepted, "Duplicate accepted source taxon key")
        accepted[key] = row["plant"]
    require(len(accepted) == 255, "Original255 accepted-name mapping changed")
    require(set(names).issubset(set(accepted.values())), "Frozen106 absent from Original255 mapping")
    header = documents["gbif_archive_header_preflight.json"]["files"]["plant"]
    require(header["doi"] == DOI and header["download_key"] == DOWNLOAD_KEY,
            "Archive receipt source identity mismatch")
    require(header["sha256"] == ARCHIVE_SHA and header["zip_size_bytes"] == ARCHIVE_SIZE,
            "Archive receipt signature mismatch")
    embargo = documents["plant_106x17_global_source_embargo_compact.json"]
    require(embargo["source_plant_GBIF_DOI"] == DOI and
            embargo["source_plant_original_zip_sha256"] == ARCHIVE_SHA and
            embargo["original_106_plant_universe_sha256"] == ROSTER_SHA,
            "Original country source audit identity mismatch")
    audit = embargo["source_row_audit"]
    require(audit["original_plant_source_rows_read"] == EXPECTED_ROWS and
            audit["total_unique_original_dataset_keys_any_country"] == EXPECTED_DATASETS,
            "Original country source audit denominator mismatch")
    qc = documents["gbif_full_source_qc_summary.json"]["groups"]["plant"]
    require(qc["doi"] == DOI and qc["archive_sha256"] == ARCHIVE_SHA,
            "Original full-QC source identity mismatch")
    return set(names), accepted, header, audit, qc


def read_archive(archive_path, focal_names, accepted, header, audit, qc):
    require(archive_path.is_file(), "--archive must be an existing local original ZIP")
    require(archive_path.stat().st_size == ARCHIVE_SIZE, "Original ZIP size mismatch")
    require(sha256_file(archive_path) == ARCHIVE_SHA, "Original ZIP SHA256 mismatch")
    countries = set(audit["source_dataset_country_counts"])
    require(len(countries) == 29, "Original country universe must have 29 countries")
    raw = defaultdict(Counter)
    strict = defaultdict(Counter)
    focal = defaultdict(Counter)
    seen_ids = set()
    rows = 0
    valid_scope_rows = 0
    missing_keys = 0
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.namelist() == [header["zip_entry_name"]], "Original ZIP member changed")
        with archive.open(header["zip_entry_name"]) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""),
                                    delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            require(reader.fieldnames == header["header_columns"], "Original source header changed")
            for row in reader:
                rows += 1
                cc = (row.get("countryCode") or "").strip()
                try:
                    year = int(row.get("year") or "")
                except (TypeError, ValueError):
                    continue
                if cc not in countries or not 2000 <= year <= 2025:
                    continue
                valid_scope_rows += 1
                ds = (row.get("datasetKey") or "").strip()
                if not ds:
                    missing_keys += 1
                    continue
                raw[cc][ds] += 1
                if not row or any(value is None for value in row.values()):
                    continue
                key = str(row.get("speciesKey") or "")
                if key not in accepted:
                    continue
                gid = (row.get("gbifID") or "").strip()
                if gid:
                    if gid in seen_ids:
                        continue
                    seen_ids.add(gid)
                try:
                    lat = float(row.get("decimalLatitude"))
                    lon = float(row.get("decimalLongitude"))
                    uncertainty = float(row.get("coordinateUncertaintyInMeters"))
                except (TypeError, ValueError):
                    continue
                if not (math.isfinite(lat) and -90 <= lat <= 90 and
                        math.isfinite(lon) and -180 <= lon <= 180 and
                        math.isfinite(uncertainty) and 0 <= uncertainty <= 12500):
                    continue
                strict[cc][ds] += 1
                if accepted[key] in focal_names:
                    focal[cc][ds] += 1
    require(rows == EXPECTED_ROWS, "Original archive row count changed")
    require(valid_scope_rows == audit["original_rows_in_fixed_29_countries_year_range"],
            "Original country/year scope changed")
    require(missing_keys == audit["source_rows_missing_datasetKey"] == 0,
            "Original source has missing datasetKey")
    require({cc: sum(values.values()) for cc, values in raw.items()} ==
            audit["source_record_country_counts"], "Original per-country row counts changed")
    require({cc: len(values) for cc, values in raw.items()} ==
            audit["source_dataset_country_counts"], "Original per-country dataset counts changed")
    require(sum(sum(values.values()) for values in strict.values()) ==
            qc["quality_flags"]["precision_known_le_12_5km"],
            "Known-precision source row count does not reproduce original QC")
    return raw, strict, focal


def global_counts(country_counts):
    result = Counter()
    for values in country_counts.values():
        result.update(values)
    return result


def get_download_membership(expected_counts):
    metadata = {}
    page_sources = []
    offset = 0
    while True:
        url = f"{METADATA_URL}?limit=1000&offset={offset}"
        data = fetch_bytes(url)
        page = json.loads(data)
        require(page["offset"] == offset and page["count"] == EXPECTED_DATASETS,
                "Download membership pagination/denominator changed")
        require(page["limit"] > 0 and page["results"], "Empty download membership page")
        for row in page["results"]:
            key = row["datasetKey"]
            require(row["downloadKey"] == DOWNLOAD_KEY and key not in metadata,
                    "Download membership duplicate or wrong download")
            metadata[key] = row
        page_sources.append({"url": url, "content_sha256": hashlib.sha256(data).hexdigest(),
                             "result_count": len(page["results"])})
        if page["endOfRecords"]:
            break
        offset += page["limit"]
        require(offset <= EXPECTED_DATASETS, "Unexpected download membership pagination")
    require(len(metadata) == EXPECTED_DATASETS and set(metadata) == set(expected_counts),
            "Download metadata dataset keys do not equal original archive keys")
    require(all(row["numberRecords"] == expected_counts[key] for key, row in metadata.items()),
            "Download metadata per-dataset counts do not equal original archive counts")
    return metadata, page_sources


def dataset_rows(metadata, raw, strict, focal):
    totals = [global_counts(counts) for counts in (raw, strict, focal)]
    rows = []
    for key, meta in sorted(metadata.items()):
        row = {
            "datasetKey": key, "datasetTitle": meta["datasetTitle"],
            "datasetDOI": meta.get("datasetDOI"),
            "publishingCountryCode": meta.get("publishingCountryCode"),
            "original_source_records_all29": totals[0][key],
            "strict255_records_all29": totals[1][key],
            "strict_focal106_records_all29": totals[2][key],
        }
        for country in FOCUS_COUNTRIES:
            row[f"original_source_records_{country}"] = raw[country][key]
            row[f"strict255_records_{country}"] = strict[country][key]
            row[f"strict_focal106_records_{country}"] = focal[country][key]
        row["dataset_url"] = f"https://www.gbif.org/dataset/{key}"
        row["download_membership_url"] = METADATA_URL
        rows.append(row)
    return rows


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archive", type=Path, required=True, help="Existing frozen original plant ZIP")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for safe dataset-level results")
    parser.add_argument("--input-dir", type=Path, help="Directory containing the five exact frozen JSON receipts; otherwise fetch immutable raw URLs")
    args = parser.parse_args(argv)
    documents, input_sources = load_inputs(args.input_dir)
    focal_names, accepted, header, audit, qc = validate_inputs(documents)
    raw, strict, focal = read_archive(args.archive, focal_names, accepted, header, audit, qc)
    total_raw, total_strict, total_focal = [global_counts(x) for x in (raw, strict, focal)]
    metadata, metadata_sources = get_download_membership(total_raw)
    all_rows = dataset_rows(metadata, raw, strict, focal)
    focus_rows = [row for row in all_rows if any(row[f"original_source_records_{cc}"] for cc in FOCUS_COUNTRIES)]
    country_summary = {
        cc: {"original_source_records": sum(raw[cc].values()), "original_source_dataset_keys": len(raw[cc]),
             "strict255_records": sum(strict[cc].values()), "strict255_dataset_keys": len(strict[cc]),
             "strict_focal106_records": sum(focal[cc].values()), "strict_focal106_dataset_keys": len(focal[cc])}
        for cc in sorted(raw)
    }
    result = {
        "schema_version": 1,
        "status": "HASH_VERIFIED_ORIGINAL_GBIF_SOURCE_REGISTRY_RECONSTRUCTED",
        "metadata_retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_repository_commit": COMMIT, "input_provenance": input_sources,
        "download_key": DOWNLOAD_KEY, "doi": DOI, "original_archive_url": ARCHIVE_URL,
        "original_zip_sha256": ARCHIVE_SHA, "original_zip_bytes": ARCHIVE_SIZE,
        "original_106_roster_sha256": ROSTER_SHA, "original_106_roster_hash_reproduced": True,
        "original_query_accepted_plant_names": len(accepted), "focal_plant_names": len(focal_names),
        "original_source_records_all29": sum(total_raw.values()), "original_source_dataset_keys_all29": len(total_raw),
        "strict255_records_all29": sum(total_strict.values()), "strict255_dataset_keys_all29": len(total_strict),
        "strict_focal106_records_all29": sum(total_focal.values()), "strict_focal106_dataset_keys_all29": len(total_focal),
        "archive_country_counts_reproduce_original_source_audit": True,
        "strict255_record_count_reproduces_original_QC": True,
        "all1202_download_metadata_keys_and_record_counts_equal_original_archive": True,
        "download_dataset_metadata_sources": metadata_sources,
        "source_country_summary": country_summary,
        "focus_countries": list(FOCUS_COUNTRIES), "CR_PA_union_dataset_keys": len(focus_rows),
        "CR_PA_dataset_registry": focus_rows,
        "record_filter_assumptions": [
            "Original source scope: all rows from the hash-verified 255-name GBIF query, years 2000-2025 and the frozen 29 countries.",
            "Country source-key membership uses all scoped source rows, regardless of coordinate uncertainty or focal106 membership.",
            "Strict255 screen: original accepted speciesKey mapping; duplicate nonempty gbifID removed in memory; valid finite coordinates; known finite uncertainty 0-12500 m inclusive.",
            "Strict focal106 screen adds only membership in the hash-verified 106-name roster.",
            "Strict counts are occurrence-row counts; they are not 25 km cells or final model training/test rows. No source-matched background subtraction, holdout embargo, raster mask, or fitted-model retention is reconstructed.",
        ],
        "interpretation_limits": [
            "DatasetKey membership establishes a source registry. Dataset titles, publisher names, and unequal keys alone do not establish independence of projects, field surveys, records, or providers.",
            "BIEN-to-GBIF project/source equivalence must be supported separately; an absent alias is not proof of disjointness.",
            "No ecological model was fit or scored. No biological validation or source-independence verdict is produced.",
        ],
        "outputs_contain_only_dataset_level_metadata_and_aggregate_counts": True,
        "raw_occurrence_rows_coordinates_or_identifiers_written": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "original_plant_gbif_CR_PA_source_registry.json"
    csv_path = args.output_dir / "original_plant_gbif_all1202_dataset_registry.csv"
    focus_path = args.output_dir / "original_plant_gbif_CR_PA_dataset_registry.csv"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(csv_path, all_rows)
    write_csv(focus_path, focus_rows)
    print(json.dumps({"status": result["status"], "original_dataset_keys": len(all_rows),
                      "CR_PA_union_dataset_keys": len(focus_rows),
                      "CR": country_summary["CR"], "PA": country_summary["PA"],
                      "files": [str(json_path), str(csv_path), str(focus_path)]}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        print(f"SOURCE_REGISTRY_ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
