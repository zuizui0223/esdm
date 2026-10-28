#!/usr/bin/env python3
"""Post-result E7-C: directly matched camera-year wet/dry diel record contrasts.

NOT a rerun of the original E7 pooled pair-MH primary endpoint or E5
detection identification. Source files are the same 11 pinned LILA COCO ZIPs;
the original parser is reused solely for identical source filtering and
per-season QC. Every exported value is an aggregate, never a site/sequence ID.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import median

MIN_SITES = 5
MIN_SITE_YEARS = 10
MIN_SOURCE_SEASONS = 3
EXPECTED_PANEL = (
    "buffalo", "elephant", "gazelleGrants", "gazelleThomsons", "giraffe",
    "hartebeest", "hyenaSpotted", "lion", "reedbuck", "warthog",
    "wildebeest", "zebra"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_within_cell_diel_changes(counts: Counter, folder_support: dict,
                                     taxa: tuple[str, ...]) -> dict:
    """Return local delta_i at camera-year only when all four bins are positive."""
    candidates = {(loc, year) for loc, year, phase, taxon, time in counts
                  if taxon in taxa}
    complete = {}
    for siteyear in sorted(candidates):
        loc, year = siteyear
        local = {}
        for taxon in taxa:
            wet_n = counts[(loc, year, "wet", taxon, "night")]
            wet_d = counts[(loc, year, "wet", taxon, "midday")]
            dry_n = counts[(loc, year, "dry", taxon, "night")]
            dry_d = counts[(loc, year, "dry", taxon, "midday")]
            if min(wet_n, wet_d, dry_n, dry_d) <= 0:
                continue
            delta = math.log(dry_n / dry_d) - math.log(wet_n / wet_d)
            local[taxon] = delta
        if local:
            source_folders = (
                set(folder_support.get((loc, year, "wet"), ())) |
                set(folder_support.get((loc, year, "dry"), ()))
            )
            complete[siteyear] = {"changes": local, "source_seasons": source_folders}
    return complete


def _eligible(rows: list[tuple[str, int, float, set]]) -> bool:
    return (len(rows) >= MIN_SITE_YEARS
            and len({x[0] for x in rows}) >= MIN_SITES
            and len(set().union(*(x[3] for x in rows))) >= MIN_SOURCE_SEASONS)


def pair_result(complete: dict, species1: str, species2: str) -> dict:
    """Single site-year comparison then equal-site-year median, no MH weighting."""
    rows = []
    for (site, year), data in complete.items():
        local = data["changes"]
        if species1 in local and species2 in local:
            rows.append((site, year, local[species1] - local[species2],
                         data["source_seasons"]))
    nsites = len({r[0] for r in rows})
    source_seasons = set().union(*(r[3] for r in rows)) if rows else set()
    result = {
        "species_1": species1, "species_2": species2,
        "eligible_matched_site_years": len(rows),
        "eligible_distinct_cameras": nsites,
        "original_source_folders": len(source_seasons),
        "status": "INSUFFICIENT_DIRECT_CELL_SUPPORT",
        "median_local_log_dry_wet_relative_diel_change": None,
        "mean_local_log_dry_wet_relative_diel_change": None,
        "fraction_local_changes_positive": None,
        "leave_one_camera": {
            "all_computable": False, "valid_deletions": 0,
            "minimum": None, "maximum": None, "sign_stable": False,
        },
    }
    if not _eligible(rows):
        return result
    values = [r[2] for r in rows]
    primary = median(values)
    out = result["leave_one_camera"]
    lvals = []
    if nsites > MIN_SITES:
        for camera in sorted({r[0] for r in rows}):
            remain = [r for r in rows if r[0] != camera]
            if _eligible(remain):
                lvals.append(median(r[2] for r in remain))
    out["all_computable"] = bool(lvals) and len(lvals) == nsites
    out["valid_deletions"] = len(lvals)
    out["minimum"] = min(lvals) if lvals else None
    out["maximum"] = max(lvals) if lvals else None
    out["sign_stable"] = bool(
        out["all_computable"] and primary != 0
        and (all(x > 0 for x in lvals) if primary > 0
             else all(x < 0 for x in lvals))
    )
    result.update({
        "status": "DESCRIPTIVE_DIRECT_CELL_ESTIMABLE",
        "median_local_log_dry_wet_relative_diel_change": primary,
        "mean_local_log_dry_wet_relative_diel_change": math.fsum(values)/len(values),
        "fraction_local_changes_positive": sum(x > 0 for x in values)/len(values),
    })
    return result


def triple_closure(complete: dict) -> dict:
    """Cell identities must close; not a biological interaction test."""
    checks = 0
    max_abs = 0.0
    cells_with_triple = 0
    for data in complete.values():
        local = data["changes"]
        if len(local) < 3:
            continue
        cells_with_triple += 1
        for a, b, c in combinations(sorted(local), 3):
            ab = local[a] - local[b]
            bc = local[b] - local[c]
            ac = local[a] - local[c]
            gap = abs(ab + bc - ac)
            checks += 1
            max_abs = max(max_abs, gap)
    if max_abs > 1e-10:
        raise ValueError("exact same-camera/year triangle identity failed")
    return {
        "complete_three_taxon_site_years": cells_with_triple,
        "triple_site_year_identity_checks": checks,
        "maximum_absolute_log_cycle_gap": max_abs,
        "expected_gap_zero_by_algebra_not_biology": True,
    }


def summarize(complete: dict, roster: tuple[str, ...]) -> dict:
    pairs = [pair_result(complete, a, b) for a, b in combinations(roster, 2)]
    supported = [p for p in pairs if p["status"]=="DESCRIPTIVE_DIRECT_CELL_ESTIMABLE"]
    return {
        "site_years_with_at_least_one_complete_taxon": len(complete),
        "species_complete_site_year_counts": {
            taxon: sum(taxon in data["changes"] for data in complete.values())
            for taxon in roster
        },
        "possible_pairs": len(pairs),
        "estimable_pairs": len(supported),
        "pairs_with_stable_sign_under_all_camera_deletions":
            sum(p["leave_one_camera"]["sign_stable"] for p in supported),
        "triple_identity": triple_closure(complete),
        "all_66_pairs_including_support_refusals": pairs,
    }


def run(archive_dir: Path, original_result: Path) -> dict:
    # Keep the primary E7 empirical record as a separately verified
    # source-consistency anchor before calculating this new estimand.
    expected_result_sha = "21a0b03d8c17442ddeeed79023ec28d23525c2815ca7a0bbaf54faec12e65f2a"
    if _sha256(original_result) != expected_result_sha:
        raise ValueError("frozen E7 result JSON sha256 changed")
    prior = json.loads(original_result.read_text(encoding="utf-8"))
    panel = tuple(sorted(prior["roster_selected_before_validation"]))
    if panel != EXPECTED_PANEL:
        raise ValueError("previously frozen discovery-only taxon panel drift")
    from scripts.e7_serengeti_wet_dry_diel import (
        DISCOVERY, VALIDATION, EXPECTED_SOURCE_SHA256, parse_season,
    )
    observed_parts = {}
    input_digests = {}
    season_qc = {}
    for label, seasons in (("discovery", DISCOVERY), ("validation", VALIDATION)):
        counts = Counter()
        folders = defaultdict(set)
        # Original occupancy is a parser side-effect, but must not reselect
        # species or alter the original discovery/validation partition.
        occupancy = defaultdict(set)
        for season in seasons:
            filename = f"SnapshotSerengetiS{season:02d}.json.zip"
            path = archive_dir / filename
            tag = f"S{season:02d}"
            digest = _sha256(path)
            if digest != EXPECTED_SOURCE_SHA256[tag]:
                raise ValueError(f"source file sha256 mismatch for {tag}")
            input_digests[tag] = digest
            qc = parse_season(path, season, counts, occupancy, folders)
            if qc != prior["source_season_qc"][tag]:
                raise ValueError(f"original E7 source parser/QC drift for {tag}")
            season_qc[tag] = "IDENTICAL_TO_FROZEN_E7"
        local = collect_within_cell_diel_changes(counts, folders, panel)
        observed_parts[label] = summarize(local, panel)

    x, y = observed_parts["discovery"], observed_parts["validation"]
    left = {(p["species_1"],p["species_2"]):p
            for p in x["all_66_pairs_including_support_refusals"]}
    transfer = []
    for p in y["all_66_pairs_including_support_refusals"]:
        key = (p["species_1"],p["species_2"])
        old = left[key]
        eligible = (old["status"] == p["status"] == "DESCRIPTIVE_DIRECT_CELL_ESTIMABLE")
        a = old["median_local_log_dry_wet_relative_diel_change"] if eligible else None
        b = p["median_local_log_dry_wet_relative_diel_change"] if eligible else None
        agrees = bool(eligible and a*b > 0)
        stable = bool(agrees and old["leave_one_camera"]["sign_stable"]
                      and p["leave_one_camera"]["sign_stable"])
        transfer.append({
            "species_1": key[0], "species_2": key[1],
            "estimable_in_both": eligible,
            "direction_concordant": agrees,
            "both_periods_camera_deletion_sign_stable": stable,
            "discovery_direct_median": a,
            "validation_direct_median": b,
        })
    both = sum(p["estimable_in_both"] for p in transfer)
    matched = sum(p["direction_concordant"] for p in transfer)
    return {
        "schema_version": 1,
        "status": "E7_POSTRESULT_DIRECT_MATCHED_CAMERA_YEAR_DESCRIPTIVE_RESULT",
        "original_empirical_run": 39222089646,
        "original_empirical_sha256": expected_result_sha,
        "original_source_archive_sha256": input_digests,
        "source_qc_agreement": season_qc,
        "original_frozen_taxa": list(panel),
        "analysis_unit": "same physical camera location x hydrological year",
        "four_species_phase_time_cells_strictly_positive": True,
        "fixed_support_rule": {
            "min_site_years": MIN_SITE_YEARS,
            "min_physical_cameras": MIN_SITES,
            "min_original_collection_seasons": MIN_SOURCE_SEASONS,
        },
        "discovery": x, "validation": y,
        "cross_period": {
            "both_estimable_pairs": both,
            "direction_agreement_pairs": matched,
            "concordant_fraction": matched/both if both else None,
            "camera_deletion_stable_direction_agreement": sum(
                p["both_periods_camera_deletion_sign_stable"] for p in transfer),
            "all_66_pairs": transfer,
        },
        "interpretation_boundary": {
            "new_endpoint_post_result_on_same_E7_biological_records": True,
            "original_E7_pair_MH_endpoint_rerun": False,
            "same_camera_year_removes_pair_specific_MH_weighting": True,
            "within_cell_triangle_closure_is_tautological": True,
            "species_specific_detection_independently_identified": False,
            "rainfall_NDVI_or_resource_covariates_joined": False,
            "animal_behavior_or_competition_causal_inference_authorized": False,
            "camera_years_not_independent_if_cameras_repeat": True,
            "no_individual_animal_inference_or_event_level_CIs": True,
            "raw_camera_location_or_sequence_keys_exported": False,
            "E4_frozen_result_changed": False,
            "E5_G4_passed": False,
            "E5_standard_qualified_datasets": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--original-e7-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.archive_dir, args.original_e7_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
                        + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "discovery_est": result["discovery"]["estimable_pairs"],
        "validation_est": result["validation"]["estimable_pairs"],
        "both_est": result["cross_period"]["both_estimable_pairs"],
        "same_direction": result["cross_period"]["direction_agreement_pairs"],
        "camera_deletion_robust_both":result["cross_period"]["camera_deletion_stable_direction_agreement"],
        "discovery_triples":result["discovery"]["triple_identity"],
        "validation_triples":result["validation"]["triple_identity"],
    },sort_keys=True))


if __name__ == "__main__":
    main()
