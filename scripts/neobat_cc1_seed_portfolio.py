"""Reproduce a Cocha Cashu seed-rain × bat-source-link pilot without bat responses.

All outputs are descriptive. The source network is global and its links are NOT
confirmed locally at CC1. Seed rain is NOT directly edible fruit biomass.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
from urllib.request import Request, urlopen

SEED_SOURCE_URL = (
    "https://raw.githubusercontent.com/pakdamie/TreePhenEcology/"
    "521b118b75af4d1bb2b7feadb28b077a09301eab/"
    "treephenecology_2023/DryadData/CC1_ALL_FINAL.csv"
)
SEED_BLOB_SHA = "dc95badb04365449e9ad5a13e8a37c5a9fc552e9"
LINK_SOURCE_URL = (
    "https://raw.githubusercontent.com/gflorezm/NeoBat_Interactions/"
    "d25292d19be32a85a21c60384a3f2d818e8081de/Data/NeoBat_Interactions_Records.csv"
)
LINK_BLOB_SHA = "71f179a152a262d7a98d7bb4e633cf136bc39f98"
LINK_SHA256 = "723198f850aa4ee7346122e71a3dd3eadaca176a65bfb87dc2a90f55f2acf10b"
ROSTER_SHA256 = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
BATS = (
    "Carollia perspicillata", "Artibeus lituratus", "Artibeus jamaicensis",
    "Sturnira lilium", "Artibeus planirostris", "Sturnira giannae",
    "Carollia brevicauda", "Artibeus phaeotis", "Sturnira parvidens",
    "Carollia castanea", "Chiroderma villosum", "Sturnira tildae",
    "Artibeus obscurus", "Platyrrhinus helleri", "Vampyressa thyone",
    "Rhinophylla pumilio", "Uroderma bilobatum", "Platyrrhinus lineatus",
    "Uroderma convexum", "Vampyriscus nymphaea", "Artibeus toltecus",
    "Artibeus watsoni", "Artibeus concolor", "Sturnira ludovici",
    "Artibeus gnomus", "Artibeus cinereus",
)
N_PERMUTATIONS = 499
RNG_SEED = 20261124


def require(value, message):
    if not value:
        raise ValueError(message)


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def fetch_original(url, expected_blob, max_bytes=1_000_000):
    with urlopen(Request(url, headers={"User-Agent": "esdm-NeoBat-CC1-replication/1"}),
                 timeout=50) as response:
        require(response.status == 200, f"SOURCE_HTTP_{response.status}")
        content = response.read(max_bytes + 1)
    require(len(content) <= max_bytes, "SOURCE_BYTE_LIMIT")
    require(git_blob_sha(content) == expected_blob, "SOURCE_BLOB_SHA_MISMATCH")
    return content


def read_cc1(data, plant_names):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    fields = reader.fieldnames
    require(fields is not None and "Group.1" in fields
            and len(fields) >= 6, "CC1_TABLE_SCHEMA")
    require(len(fields) == len(set(fields)), "CC1_DUPLICATE_COLUMN")
    ignored = {"", "Group.1", "Day_Length", "Day_Year", "Day_Year_Y"}
    names = {name.casefold().replace("_", " ", 1): name for name in fields
             if name not in ignored}
    eligible = set(names) & plant_names
    require(len(eligible) == len({names[k] for k in eligible}), "CC1_AMBIGUOUS_MATCH")
    rows = list(reader)
    require(len(rows) > 0, "CC1_NO_OBSERVATION_ROWS")
    observed = {}
    missing = negative = 0
    zeros = positives = 0
    for row in rows:
        dt = date.fromisoformat(row["Group.1"])
        key = dt.isoformat()
        require(key not in observed, "CC1_DUPLICATE_SAMPLE_DATE")
        vals = {}
        for name in eligible:
            raw = row[names[name]]
            if raw is None or raw.strip() in ("", "NA", "NaN", "NULL"):
                vals[name] = None
                missing += 1
                continue
            value = float(raw)
            require(math.isfinite(value) and value >= 0, "CC1_NEGATIVE_OR_INVALID_SEED_COUNT")
            vals[name] = value
            zeros += (value == 0)
            positives += (value > 0)
        observed[key] = vals
    return {
        "matched": sorted(eligible), "rows": observed, "species_columns": len(fields) - 5,
        "missing_matched_cells": missing, "zero_matched_cells": zeros,
        "positive_matched_cells": positives,
    }


def read_neobat_links(data, plant_names):
    require(git_blob_sha(data) == LINK_BLOB_SHA, "LINK_BLOB_ID_DRIFT")
    require(hashlib.sha256(data).hexdigest() == LINK_SHA256, "LINK_SHA256_DRIFT")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    records = list(reader)
    require(len(records) == 2571, "SOURCE_2571_LINK_RECORDS_DRIFT")
    links = {bat: set() for bat in BATS}
    hits = 0
    for r in records:
        bat = r["CurrentBatSpecies"].strip()
        plant = r["CurrentPlantSpecies"].strip().casefold()
        if (bat in links and plant in plant_names and
            r["Interaction"].strip().casefold() == "frugivory" and
            r["TrophicGuild"].strip().casefold() == "frugivore"):
            links[bat].add(plant)
            hits += 1
    return links, hits


def xorshift32(s):
    s = (s ^ (s << 13)) & 0xffffffff
    s ^= s >> 17
    return (s ^ (s << 5)) & 0xffffffff


def cv(x):
    mean = statistics.mean(x)
    return statistics.stdev(x) / mean if len(x) >= 2 and mean > 0 else None


def portfolio(bat, species, sample, n_perm=N_PERMUTATIONS):
    dates = sorted(sample["rows"]) if species else []
    shared = [day for day in dates if all(sample["rows"][day][sp] is not None for sp in species)]
    rec = {"bat": bat, "source_linked_CC1_plants": len(species),
           "plant_names": sorted(species), "shared_dates": len(shared),
           "eligible": False, "observed_CV": None,
           "shift_null_median_CV": None, "CV_ratio": None,
           "status": "INSUFFICIENT_PLANTS_OR_SHARED_DATES"}
    if len(species) < 3 or len(shared) < 60:
        return rec
    arrays = []
    for sp in sorted(species):
        vals = [math.log1p(sample["rows"][day][sp]) for day in shared]
        avg = statistics.mean(vals)
        if avg <= 0:
            rec["status"] = "ZERO_LOG_SEED_OUTPUT"
            return rec
        arrays.append([x / avg for x in vals])
    observed = [statistics.mean(vals) for vals in zip(*arrays)]
    obs_cv = cv(observed)
    require(obs_cv is not None, "NO_PORTFOLIO_MEAN")
    state = RNG_SEED
    nulls = []
    n = len(shared)
    for _ in range(n_perm):
        shifts = []
        for _ in arrays:
            state = xorshift32(state)
            shifts.append(state % n)
        shifted = [statistics.mean(array[(i + shifts[j]) % n]
                                  for j, array in enumerate(arrays))
                   for i in range(n)]
        nulls.append(cv(shifted))
    null_med = statistics.median(nulls)
    require(null_med is not None and null_med > 0, "SHIFT_NULL_ZERO_CV")
    rec.update({"eligible": True, "observed_CV": obs_cv,
                "shift_null_median_CV": null_med, "CV_ratio": obs_cv/null_med,
                "status": ("MORE_COMPENSATORY_THAN_SHIFT_MEDIAN"
                           if obs_cv < null_med else
                           "MORE_SYNCHRONOUS_THAN_SHIFT_MEDIAN"
                           if obs_cv > null_med else "EQUAL_TO_SHIFT_MEDIAN")})
    return rec


def evaluate(seed_bytes, link_bytes, manifest):
    names = {x.casefold() for x in manifest["plant_taxa"]}
    require(len(names) == 106 and manifest["source_fixed106_sha256"] == ROSTER_SHA256,
            "FROZEN_106_PLANT_ROSTER_DRIFT")
    require(git_blob_sha(seed_bytes) == SEED_BLOB_SHA, "CC1_SOURCE_BLOB_MISMATCH")
    samples = read_cc1(seed_bytes, names)
    links, hits = read_neobat_links(link_bytes, names)
    profiles = [portfolio(b, links[b] & set(samples["matched"]), samples) for b in BATS]
    dates = sorted(samples["rows"])
    return {"schema_version": 1, "status": "CC1_ORIGINAL_PUBLISHED_SEED_TIME_SERIES_DIAGNOSTIC",
            "source": {
                "site": "Cocha Cashu, Peru",
                "paper_doi": "10.1002/ecy.4022",
                "source_github_commit": "521b118b75af4d1bb2b7feadb28b077a09301eab",
                "source_file": "treephenecology_2023/DryadData/CC1_ALL_FINAL.csv",
                "source_blob_sha": SEED_BLOB_SHA,
                "link_source_github_commit": "d25292d19be32a85a21c60384a3f2d818e8081de",
                "link_file_sha256": LINK_SHA256,
                "link_file_blob_sha": LINK_BLOB_SHA,
                "original_106_roster_sha256": ROSTER_SHA256,
            },
            "sampling": {
                "observation_events": len(dates),
                "earliest": dates[0], "latest": dates[-1],
                "published_species_columns": samples["species_columns"],
                "fixed106_exact_matched_species": len(samples["matched"]),
                "fixed106_matched_names": samples["matched"],
                "matched_numeric_cells": (samples["zero_matched_cells"] +
                                          samples["positive_matched_cells"]),
                "matched_positive_cells": samples["positive_matched_cells"],
                "matched_zero_cells": samples["zero_matched_cells"],
                "matched_missing_cells": samples["missing_matched_cells"],
                "original_neo_fruit_records_to_fixed106": hits,
            },
            "portfolios": {
                "candidate_bat_denominator": len(BATS),
                "evaluable": sum(p["eligible"] for p in profiles),
                "more_synchronous": sum(p["status"] == "MORE_SYNCHRONOUS_THAN_SHIFT_MEDIAN"
                                        for p in profiles),
                "more_compensatory": sum(p["status"] == "MORE_COMPENSATORY_THAN_SHIFT_MEDIAN"
                                         for p in profiles),
                "per_candidate_bat": profiles,
            },
            "limits": {
                "single_peru_site_only": True,
                "global_neo_links_are_not_locally_verified_CC1_bat_diet": True,
                "seed_counts_are_not_edible_ripe_fruit_mass": True,
                "shared_species_make_bat_profiles_dependent": True,
                "circular_shift_null_does_not_control_shared_seasonality": True,
                "not_m3_or_bat_predictive_performance": True,
                "not_formal_p_value_test": True,
            }}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"status": "SOURCE_NOT_EVALUABLE"}
    try:
        a = fetch_original(SEED_SOURCE_URL, SEED_BLOB_SHA)
        b = fetch_original(LINK_SOURCE_URL, LINK_BLOB_SHA)
        m = json.loads(args.manifest.read_text(encoding="utf-8"))
        receipt = evaluate(a, b, m)
    except Exception as exc:
        receipt = {"status": "CC1_PUBLIC_SOURCE_OR_SCHEMA_STOP",
                   "error_type": type(exc).__name__, "error_code": str(exc)[:220],
                   "bat_model_fitted": False}
    args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(receipt["status"], receipt.get("error_code", ""), flush=True)
    return 0 if receipt["status"] == "CC1_ORIGINAL_PUBLISHED_SEED_TIME_SERIES_DIAGNOSTIC" else 3


if __name__ == "__main__":
    raise SystemExit(main())
