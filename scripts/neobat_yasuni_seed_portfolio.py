"""Second original field site: Yasuní seed rain × fixed NeoBat source-linked portfolios.

Companion to the pre-existing CC1 result, not an independent bat sample.
The original author-cleaned long CSV and taxonomy bridge must match Git blobs.
No raw observations, coordinates or personal data enter output receipts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from itertools import combinations
import hashlib
import io
import json
import math
from pathlib import Path
import statistics

from scripts.neobat_cc1_seed_portfolio import (
    BATS, LINK_BLOB_SHA, LINK_SHA256, LINK_SOURCE_URL, ROSTER_SHA256,
    fetch_original, git_blob_sha, portfolio,
)
from scripts.neobat_cc1_size_matched_control import observed_portfolio_cv

AUTHOR_COMMIT = "521b118b75af4d1bb2b7feadb28b077a09301eab"
AUTHOR_ROOT = ("https://raw.githubusercontent.com/pakdamie/TreePhenEcology/" +
               AUTHOR_COMMIT + "/treephenecology_2023/DryadData/")
YAS_URL = AUTHOR_ROOT + "YASUNI_ALL_FINAL.csv"
TAXON_URL = AUTHOR_ROOT + "Family/YAS_FAMILY_CODE.csv"
YAS_BLOB = "11cafba9ae138605fdd79cea7a31bc4821d869ee"
TAXON_BLOB = "d9e017afc326059d5feb8f89e4a17bd079f52301"
YAS_BYTES = 14_572_057
PREOUTCOME_COMMIT = "a4e90d778a7ef086af8675c8a4d16bb2b7a0eb84"


def require(value, msg):
    if not value:
        raise ValueError(msg)


def link_names_to_author_codes(taxon_bytes, fixed_106):
    require(git_blob_sha(taxon_bytes) == TAXON_BLOB, "AUTHOR_TAXON_GIT_BLOB_MISMATCH")
    reader = csv.DictReader(io.StringIO(taxon_bytes.decode("utf-8-sig")))
    need = {"CODIGO", "Taxon.NombreActual"}
    require(reader.fieldnames is not None and need <= set(reader.fieldnames),
            "TAXON_BRIDGE_REQUIRED_COLUMNS_MISSING")
    code_to_name = {}
    name_to_code = {}
    matched = []
    for row in reader:
        code = (row["CODIGO"] or "").strip()
        name = (row["Taxon.NombreActual"] or "").strip().casefold()
        if name not in fixed_106:
            continue
        require(code, "MATCHED_AUTHOR_TAXON_CODE_MISSING")
        require(name_to_code.get(name, code) == code, "CONFLICTING_CODES_FOR_ONE_NAME")
        require(code_to_name.get(code, name) == name, "CONFLICTING_NAMES_FOR_ONE_CODE")
        name_to_code[name], code_to_name[code] = code, name
        matched.append((name, code))
    require(len(name_to_code) == len(code_to_name) == len(set(matched)),
            "AUTHOR_TAXON_BRIDGE_AMBIGUOUS")
    return code_to_name


def parse_yasuni(yas_bytes, code_to_name):
    """Stream long source table; preserve source numeric zeros versus missing."""
    require(git_blob_sha(yas_bytes) == YAS_BLOB, "YASUNI_SOURCE_GIT_BLOB_MISMATCH")
    require(len(yas_bytes) == YAS_BYTES, "YASUNI_SOURCE_BYTE_SIZE_CHANGED")
    reader = csv.DictReader(io.StringIO(yas_bytes.decode("utf-8-sig")))
    require(reader.fieldnames is not None and
            {"Day_Year_Y", "variable", "value"} <= set(reader.fieldnames),
            "YASUNI_LONG_SOURCE_REQUIRED_COLUMNS_MISSING")
    all_times = set()
    all_codes = set()
    observed = {}
    matched_codes = set()
    rows = 0
    missing = 0
    positive = 0
    zeros = 0
    for row in reader:
        rows += 1
        raw_time = (row["Day_Year_Y"] or "").strip()
        value_t = float(raw_time)
        require(math.isfinite(value_t) and 0 < value_t < 20,
                "YASUNI_INVALID_OR_OUT_OF_SCOPE_TIME")
        code = (row["variable"] or "").strip()
        require(code, "YASUNI_EMPTY_SOURCE_TAXON_CODE")
        all_times.add(raw_time)
        all_codes.add(code)
        if code not in code_to_name:
            continue
        matched_codes.add(code)
        name = code_to_name[code]
        key = (name, raw_time)
        require(key not in observed, "YASUNI_DUPLICATE_MATCHED_CODE_TIMEPOINT")
        raw_value = row["value"]
        if raw_value is None or raw_value.strip() in ("", "NA", "NaN", "NULL"):
            observed[key] = None
            missing += 1
        else:
            v = float(raw_value)
            require(math.isfinite(v) and v >= 0, "YASUNI_INVALID_SEED_COUNT")
            observed[key] = v
            zeros += v == 0
            positive += v > 0
    require(rows > 0 and len(all_times) > 0 and len(all_codes) > 0, "YASUNI_SOURCE_EMPTY")
    matched = sorted(code_to_name[code] for code in matched_codes)
    series = {}
    # Missing rows are missing, NEVER zero: unlike a wide observed-zero entry.
    for time in sorted(all_times, key=lambda t: float(t)):
        series[time] = {name: observed.get((name, time)) for name in matched}
    return {"rows": series, "matched": matched, "source_records": rows,
            "timepoints": len(all_times), "source_taxon_codes": len(all_codes),
            "matched_numeric_values": zeros + positive,
            "matched_zero_values": zeros,
            "matched_positive_values": positive,
            "matched_explicit_missing_values": missing,
            "matched_omitted_code_timepoints":
                len(all_times) * len(matched) - len(observed),
            "time_range_fractional_study_years": [
                min(float(x) for x in all_times), max(float(x) for x in all_times)]}


def control_for_candidate_sets(pool, result, sample):
    """Before-opened source-based size-matched descriptive control, no p-values."""
    by_size = {}
    for n in sorted({len(x["plant_names"]) for x in result if x["eligible"]}):
        all_sets = list(combinations(pool, n))
        values = []
        for plants in all_sets:
            value, dates = observed_portfolio_cv(plants, sample)
            if value is not None and dates >= 60:
                values.append(value)
        complete = len(values) == len(all_sets)
        by_size[n] = {"plant_count": n, "all_combinations": len(all_sets),
                      "evaluable_combinations": len(values),
                      "complete_baseline": complete,
                      "baseline_CV_median": statistics.median(values) if complete else None,
                      "baseline_values": sorted(values) if complete else None}
    control = []
    groups = {}
    for item in result:
        out = {"bat": item["bat"], "plants": item["plant_names"],
               "source_linked_plants": item["source_linked_CC1_plants"],
               "eligible": item["eligible"], "same_size_CV_ratio": None,
               "inclusive_CV_rank_fraction_not_pvalue": None,
               "status": "INELIGIBLE"}
        if item["eligible"]:
            k = len(item["plant_names"])
            base = by_size[k]
            key = "|".join(item["plant_names"])
            groups.setdefault(key, []).append(item["bat"])
            if base["complete_baseline"]:
                obs = item["observed_CV"]
                vals = base["baseline_values"]
                ties_or_lower = sum(v <= obs + 1e-12 for v in vals)
                q = ties_or_lower / len(vals)
                med = base["baseline_CV_median"]
                out.update({"same_size_CV_ratio": obs / med,
                            "inclusive_CV_rank_fraction_not_pvalue": q,
                            "status": ("MORE_STABLE_THAN_SAME_SIZE_MEDIAN"
                                       if obs < med - 1e-12 else
                                       "LESS_STABLE_THAN_SAME_SIZE_MEDIAN"
                                       if obs > med + 1e-12 else "EQUAL_SAME_SIZE_MEDIAN")})
            else:
                out["status"] = "INCOMPLETE_BASELINE_DO_NOT_INFER"
        control.append(out)
    return {
        "all_candidate_bats": control,
        "baseline_by_size": [
            {key: val for key, val in obj.items() if key != "baseline_values"}
            for _, obj in sorted(by_size.items())],
        "distinct_evaluable_source_plant_sets": len(groups),
        "identical_source_plant_set_groups":
            [{"plants": k.split("|"), "bat_candidates": b}
             for k, b in groups.items() if len(b) > 1]}


def evaluate(yas, taxa_bytes, neo_bytes, roster, cc1_receipt):
    names = {x.casefold() for x in roster["plant_taxa"]}
    require(len(names) == 106 and roster["source_fixed106_sha256"] == ROSTER_SHA256,
            "FROZEN_106_PLANTS_CHANGED")
    require(cc1_receipt["status"] == "CC1_ORIGINAL_PUBLISHED_SEED_TIME_SERIES_DIAGNOSTIC",
            "PREVIOUS_CC1_RESULT_NOT_VERIFIED")
    original_bat_order = [x["bat"] for x in cc1_receipt["portfolios"]["per_candidate_bat"]]
    require(original_bat_order == list(BATS), "ORIGINAL_26_BAT_ROSTER_CHANGED")
    require(git_blob_sha(neo_bytes) == LINK_BLOB_SHA and
            hashlib.sha256(neo_bytes).hexdigest() == LINK_SHA256, "NEOBAT_SOURCE_DRIFT")
    code_to_name = link_names_to_author_codes(taxa_bytes, names)
    sample = parse_yasuni(yas, code_to_name)
    # Reuse tested canonical NeoBat link parser, retained exact source semantics.
    from scripts.neobat_cc1_seed_portfolio import read_neobat_links
    links, _ = read_neobat_links(neo_bytes, names)
    matched = set(sample["matched"])
    profiles = [portfolio(bat, links[bat] & matched, sample) for bat in BATS]
    ctrl = control_for_candidate_sets(sorted(matched), profiles, sample)
    cc1_set = set(cc1_receipt["sampling"]["fixed106_matched_names"])
    return {
        "schema_version": 1,
        "status": "YASUNI_ORIGINAL_SEED_FALL_AND_SOURCELINK_PORTFOLIO_COMPLETE",
        "source": {"paper_doi": "10.1002/ecy.4022",
                   "author_original_commit": AUTHOR_COMMIT,
                   "YASUNI_original_git_blob": YAS_BLOB,
                   "taxon_bridge_original_git_blob": TAXON_BLOB,
                   "NeoBat_original_csv_sha256": LINK_SHA256,
                   "fixed_106_species_sha256": ROSTER_SHA256,
                   "preoutcome_frozen_commit": PREOUTCOME_COMMIT},
        "sampling": {key: value for key, value in sample.items() if key != "rows"},
        "candidate_species_from_author_taxon_bridge": len(code_to_name),
        "candidate_species_not_found_in_final_YASUNI_timeseries":
            sorted(set(code_to_name.values()) - matched),
        "cross_site_exact_species": sorted(matched & cc1_set),
        "all_26_source_bat_portfolios": profiles,
        "evaluable_bat_labels": sum(x["eligible"] for x in profiles),
        "unique_plant_sets": ctrl["distinct_evaluable_source_plant_sets"],
        "same_size_control": ctrl,
        "interpretation": {
            "original_YASUNI_family_censoring_applies_before_file": True,
            "YASUNI_CC1_same_paper_not_independent_studies": True,
            "global_source_links_not_confirmed_YASUNI_diets": True,
            "seed_trap_fall_not_ripe_fruit_biomass": True,
            "temporal_shifts_do_not_control_shared_seasonality": True,
            "timepoints_source_fractional_year_not_exact_dates": True,
            "missing_rows_not_filled_with_zero": True,
            "size_control_descriptive_fraction_not_pvalue": True,
            "bat_outcomes_and_M3_M1_N1_not_estimated": True},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--prior-cc1", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        yas = fetch_original(YAS_URL, YAS_BLOB, max_bytes=16_000_000)
        taxa = fetch_original(TAXON_URL, TAXON_BLOB)
        neo = fetch_original(LINK_SOURCE_URL, LINK_BLOB_SHA)
        roster = json.loads(args.manifest.read_text(encoding="utf-8"))
        cc1 = json.loads(args.prior_cc1.read_text(encoding="utf-8"))
        receipt = evaluate(yas, taxa, neo, roster, cc1)
    except Exception as exc:
        receipt = {"schema_version": 1, "status": "YASUNI_ORIGINAL_SOURCE_OR_SCHEMA_STOP",
                   "error_type": type(exc).__name__, "error_code": str(exc)[:300],
                   "no_bat_outcome_estimated": True}
    args.out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(receipt["status"], receipt.get("error_code", ""), flush=True)
    return 0 if receipt["status"] == "YASUNI_ORIGINAL_SEED_FALL_AND_SOURCELINK_PORTFOLIO_COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
