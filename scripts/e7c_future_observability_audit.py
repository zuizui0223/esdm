#!/usr/bin/env python3
"""Frozen E7-C result-only feasibility audit; no wildlife source re-opening.

This is post-outcome observational support accounting. Theoretical shortfalls
describe a NEW prospective experiment and cannot rescue the old E7-C endpoint.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

PINNED_SOURCE_SHA256 = "a032635e1acfabd89c253fe52308469735c4e13776ae3f49b7294cded9e7b6cf"
E7C_STATUS = "E7_POSTRESULT_DIRECT_MATCHED_CAMERA_YEAR_DESCRIPTIVE_RESULT"
MIN_CAMERA_YEARS = 10
MIN_CAMERAS = 5
MIN_COLLECTION_FOLDERS = 3
COHORTS = ("discovery", "validation")


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def shortfalls(row: dict) -> dict:
    n = row["eligible_matched_site_years"]
    cameras = row["eligible_distinct_cameras"]
    folders = row["original_source_folders"]
    if any(type(x) is not int or x < 0 for x in (n, cameras, folders)):
        raise ValueError("support must be nonnegative integers")
    if cameras > n or folders > 6:
        raise ValueError("impossible source support geometry")
    eligible = n >= MIN_CAMERA_YEARS and cameras >= MIN_CAMERAS and folders >= MIN_COLLECTION_FOLDERS
    if eligible != (row["status"] == "DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"):
        raise ValueError("source gate/status mismatch")
    if not eligible and row["status"] != "INSUFFICIENT_DIRECT_CELL_SUPPORT":
        raise ValueError("unknown source refusal status")
    gaps = {
        "missing_complete_camera_years": max(0, MIN_CAMERA_YEARS-n),
        "missing_distinct_camera_sites": max(0, MIN_CAMERAS-cameras),
        "missing_original_collection_folders": max(0, MIN_COLLECTION_FOLDERS-folders),
    }
    return {
        "complete_camera_years": n,
        "distinct_camera_sites": cameras,
        "original_collection_folders": folders,
        "original_estimable": eligible,
        **gaps,
        "hypothetical_future_minimum_extra_fully_observed_camera_years": max(gaps.values()),
    }


def toy_complete_probability(expected_events_per_cell: float) -> float:
    """One pair requires all eight independently Poisson-positive cells."""
    lam = expected_events_per_cell
    if not math.isfinite(lam) or lam < 0:
        raise ValueError("expected count must be finite and nonnegative")
    return (-math.expm1(-lam))**8


def expected_per_cell_for_probability(p: float) -> float:
    if not 0 < p < 1:
        raise ValueError("probability must be between 0 and 1")
    return -math.log1p(-p**(1/8))


def evaluate(source: dict) -> dict:
    if source.get("status") != E7C_STATUS:
        raise ValueError("frozen E7-C result status drift")
    taxa = source["original_frozen_taxa"]
    if len(taxa) != 12 or sorted(set(taxa)) != taxa:
        raise ValueError("original 12-taxon roster drift")
    pairs_expected = set(combinations(taxa,2))
    periods = {}
    pair_maps = {}
    for cohort in COHORTS:
        z = source[cohort]
        rows = z["all_66_pairs_including_support_refusals"]
        if len(rows) != 66:
            raise ValueError("frozen 66-pair universe changed")
        mapped = {}
        for row in rows:
            k = row["species_1"], row["species_2"]
            if k in mapped:
                raise ValueError("duplicate source pair")
            mapped[k] = row
        if set(mapped) != pairs_expected:
            raise ValueError("missing/extra source pair")
        pair_maps[cohort] = mapped
        audits = [shortfalls(row) for row in rows]
        eligible = sum(r["original_estimable"] for r in audits)
        if eligible != z["estimable_pairs"]:
            raise ValueError("original E7-C estimable-count mismatch")
        counts = Counter(
            "0" if r["complete_camera_years"]==0 else
            "1-4" if r["complete_camera_years"]<5 else
            "5-9" if r["complete_camera_years"]<10 else
            "10+" for r in audits
        )
        species_support = z["species_complete_site_year_counts"]
        if set(species_support) != set(taxa):
            raise ValueError("original species site-year coverage mismatch")
        periods[cohort] = {
            "pair_universe": 66,
            "original_estimable": eligible,
            "pair_count_by_complete_camera_year": {
                k: counts[k] for k in ("0", "1-4", "5-9", "10+")
            },
            "pairs_missing_only_ten_camera_year_minimum": sum(
                not r["original_estimable"] and r["missing_distinct_camera_sites"]==0
                and r["missing_original_collection_folders"]==0 for r in audits
            ),
            "pairs_one_complete_camera_year_short_all_other_gates_pass": sum(
                r["missing_complete_camera_years"]==1
                and r["missing_distinct_camera_sites"]==0
                and r["missing_original_collection_folders"]==0 for r in audits
            ),
            "complete_four_positive_bin_camera_years_per_species": {
                t: species_support[t] for t in taxa
            },
            "species_without_one_complete_four_positive_bin_camera_year": [
                t for t in taxa if species_support[t] == 0
            ],
        }
    pair_deficits = []
    for a, b in sorted(pairs_expected):
        d = {p:shortfalls(pair_maps[p][a,b]) for p in COHORTS}
        pair_deficits.append({
            "species_1":a,"species_2":b,
            "discovery":d["discovery"],"validation":d["validation"],
            "both_originally_estimable":all(d[p]["original_estimable"] for p in COHORTS),
            "hypothetical_future_total_lower_bound_two_separate_partitions":sum(
                d[p]["hypothetical_future_minimum_extra_fully_observed_camera_years"]
                for p in COHORTS
            ),
        })
    originally_both = sum(row["both_originally_estimable"] for row in pair_deficits)
    if originally_both != source["cross_period"]["both_estimable_pairs"]:
        raise ValueError("frozen cross-period support count mismatch")
    almost = sorted(
        (r for r in pair_deficits if not r["both_originally_estimable"]),
        key=lambda x:(x["hypothetical_future_total_lower_bound_two_separate_partitions"],
                      x["species_1"],x["species_2"])
    )
    return {
        "schema_version":1,
        "status":"E7C_FROZEN_AGGREGATE_FUTURE_OBSERVABILITY_AUDIT",
        "original_E7C_empirical_result_sha256":PINNED_SOURCE_SHA256,
        "original_fixed_gates":{
            "min_complete_camera_years":MIN_CAMERA_YEARS,
            "min_distinct_camera_sites":MIN_CAMERAS,
            "min_original_collection_folders":MIN_COLLECTION_FOLDERS,
            "strictly_positive_sequence_cells_per_pair_camera_year":8,
        },
        "periods":periods,
        "pairs_estimable_in_both_original_partitions":originally_both,
        "all_66_pair_support_and_future_shortfalls":pair_deficits,
        "ten_closest_not_qualified_pairs_by_prospective_support_only":almost[:10],
        "illustrative_poisson_sampling":{
            "assumption":"Eight independent equal-mean Poisson counts, one for each taxon x wet/dry x night/midday cell; NOT fitted or calibrated to E7 data.",
            "probability_all_eight_positive_if_per_cell_expected_events":{
                str(x):toy_complete_probability(x) for x in (1,2,3,4)
            },
            "expected_events_per_each_cell_for_all_eight_positive_probability":{
                str(x):expected_per_cell_for_probability(x) for x in (0.8,0.9)
            },
            "maximum_all_eight_positive_probability_with_one_0_2_expected_event_cell":
                -math.expm1(-0.2),
        },
        "interpretation_boundary":{
            "no_new_animal_record_or_camera_ID_opened":True,
            "not_a_refit_or_reinterpretation_of_original_E7C_endpoint":True,
            "strict_positive_cell_selection_may_depend_on_species_diel_behavior_and_detection":True,
            "future_shortfalls_are_mathematical_lower_bounds_not_feasible_survey_guarantees":True,
            "cannot_add_source_folders_or_observations_to_original_frozen_E7C_partitions":True,
            "true_passage_vs_camera_detection_and_effort_unidentified":True,
            "poisson_probabilities_are_independent_theoretical_scenarios_only":True,
            "no_inferential_CI_or_p_value":True,
            "E4_E5_E7_historical_results_unchanged":True,
        },
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-e7c",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if digest(args.original_e7c) != PINNED_SOURCE_SHA256:
        raise ValueError("frozen E7-C original result SHA256 mismatch")
    result=evaluate(json.loads(args.original_e7c.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "discovery":result["periods"]["discovery"]["pair_count_by_complete_camera_year"],
        "validation":result["periods"]["validation"]["pair_count_by_complete_camera_year"],
        "both_originally_eligible":result["pairs_estimable_in_both_original_partitions"],
    },sort_keys=True))


if __name__=="__main__":
    main()
