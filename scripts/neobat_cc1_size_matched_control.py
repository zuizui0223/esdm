"""Post-hoc, exhaustive, size-matched plant-portfolio control at Cocha Cashu.

This is an exploratory counterfactual, not a bat validation, a p-value, or a
confirmed local diet. First source-backed result and original sample time
series are checked before contrasting linked sets against ALL combinations
of the same size among the original eleven exact-matched plant taxa.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
import math
from pathlib import Path
import statistics

from scripts.neobat_cc1_seed_portfolio import (
    BATS, LINK_BLOB_SHA, LINK_SOURCE_URL, SEED_BLOB_SHA, SEED_SOURCE_URL,
    fetch_original, read_cc1, read_neobat_links, cv,
)


def require(x, msg):
    if not x:
        raise ValueError(msg)


def observed_portfolio_cv(species, samples, minimum_dates=60):
    taxa = tuple(sorted(species))
    if not taxa:
        return None, 0
    days = [day for day, row in sorted(samples["rows"].items())
            if all(row[sp] is not None for sp in taxa)]
    if len(days) < minimum_dates:
        return None, len(days)
    cols = []
    for sp in taxa:
        vals = [math.log1p(samples["rows"][d][sp]) for d in days]
        m = statistics.mean(vals)
        if m <= 0:
            return None, len(days)
        cols.append([x / m for x in vals])
    series = [statistics.mean(x) for x in zip(*cols)]
    return cv(series), len(days)


def size_matched_summary(pool, sizes, samples):
    """Enumerate every subset; no score-based selection or Monte Carlo threshold."""
    by_k = {}
    for k in sorted(set(sizes)):
        require(3 <= k <= len(pool), f"invalid candidate portfolio size {k}")
        combos = list(combinations(sorted(pool), k))
        cv_values = []
        for combo in combos:
            value, n = observed_portfolio_cv(combo, samples)
            require(value is not None and n >= 60,
                    f"invalid or insufficient joint data for exact {k}-species control")
            cv_values.append(value)
        require(len(cv_values) == math.comb(len(pool), k), "combination denominator drift")
        by_k[k] = sorted(cv_values)
    return by_k


def build_control(first, seed_bytes, link_bytes, manifest):
    require(first["status"] == "CC1_ORIGINAL_PUBLISHED_SEED_TIME_SERIES_DIAGNOSTIC",
            "prior result is not complete")
    require(first["source"]["source_blob_sha"] == SEED_BLOB_SHA and
            first["source"]["link_file_blob_sha"] == LINK_BLOB_SHA,
            "prior result source identity drift")
    names = {s.casefold() for s in manifest["plant_taxa"]}
    require(len(names) == 106, "prior fixed plant roster altered")
    samples = read_cc1(seed_bytes, names)
    pool = sorted(samples["matched"])
    require(pool == first["sampling"]["fixed106_matched_names"],
            "matched plant universe drift")
    require(len(pool) == 11 and len(samples["rows"]) == 196,
            "original CC1 source dimensions drift")
    links, _ = read_neobat_links(link_bytes, names)
    previous = first["portfolios"]["per_candidate_bat"]
    require(len(previous) == len(BATS) == 26 and [x["bat"] for x in previous] == list(BATS),
            "candidate bat universe drift")
    eligible = []
    for old in previous:
        bat = old["bat"]
        partners = sorted(links[bat] & set(pool))
        require(old["plant_names"] == partners and old["source_linked_CC1_plants"] == len(partners),
                f"{bat}: source partner set drift")
        if not old["eligible"]:
            require(len(partners) < 3 or old["shared_dates"] < 60 or
                    old["status"] == "ZERO_LOG_SEED_OUTPUT",
                    f"{bat}: unexpected ineligible first receipt")
            continue
        obs, days = observed_portfolio_cv(partners, samples)
        require(days == old["shared_dates"] and
                obs is not None and math.isclose(obs, old["observed_CV"],
                                                 rel_tol=1e-12, abs_tol=1e-12),
                f"{bat}: original observed CV drift")
        eligible.append((bat, tuple(partners), obs))
    by_k = size_matched_summary(pool, [len(p) for _, p, _ in eligible], samples)
    results = []
    groups = {}
    for bat, partners, observed in eligible:
        base = by_k[len(partners)]
        smaller = sum(x < observed - 1e-12 for x in base)
        ties = sum(math.isclose(x, observed, rel_tol=0, abs_tol=1e-12) for x in base)
        # Inclusive fraction is a descriptive percentile, NOT a significance p-value.
        q = (smaller + ties) / len(base)
        k = "|".join(partners)
        groups.setdefault(k, []).append(bat)
        results.append({"bat": bat, "plants": list(partners), "plant_count": len(partners),
                        "observed_portfolio_CV": observed,
                        "complete_same_size_combination_count": len(base),
                        "baseline_CV_median": statistics.median(base),
                        "observed_divided_by_baseline_median": observed / statistics.median(base),
                        "baseline_CV_minimum": min(base), "baseline_CV_maximum": max(base),
                        "fraction_combinations_with_CV_less_or_equal": q,
                        "rank_ties_including_self": ties,
                        "direction": ("MORE_STABLE_THAN_SIZE_MATCHED_MEDIAN"
                                      if observed < statistics.median(base) else
                                      "LESS_STABLE_THAN_SIZE_MATCHED_MEDIAN"
                                      if observed > statistics.median(base) else
                                      "EQUAL_TO_SIZE_MATCHED_MEDIAN")})
    all_candidates = []
    reg = {r["bat"]: r for r in results}
    for bat in BATS:
        all_candidates.append(reg.get(bat, {"bat": bat, "status": "INELIGIBLE_UNCHANGED",
                                            "plants": first["portfolios"]["per_candidate_bat"][
                                                BATS.index(bat)]["plant_names"],
                                            "observed_portfolio_CV": None,
                                            "fraction_combinations_with_CV_less_or_equal": None}))
    return {
        "schema_version": 1,
        "status": "CC1_POSTHOC_SIZE_MATCHED_CONTROL_COMPLETE",
        "source": {"original_cc1_github_blob_sha": SEED_BLOB_SHA,
                   "original_neobat_github_blob_sha": LINK_BLOB_SHA,
                   "frozen_primary_result": "docs/replication/neobat/cc1_original_seed_portfolio_result_20261124.json"},
        "sampling": {"matched_frozen_106_plants": len(pool),
                     "sample_dates": len(samples["rows"]),
                     "candidate_bats": len(BATS),
                     "evaluable_candidate_labels": len(eligible),
                     "distinct_candidate_plant_sets": len(groups),
                     "same_size_source_universe": len(pool)},
        "baseline_sizes": [
            {"plant_count": k, "all_combinations": len(v),
             "baseline_CV_median": statistics.median(v),
             "baseline_CV_min": min(v), "baseline_CV_max": max(v)}
            for k, v in sorted(by_k.items())],
        "source_duplicate_partner_set_groups": [
            {"plants": key.split("|"), "bat_labels": labels}
            for key, labels in groups.items() if len(labels) > 1],
        "all_candidate_bat_results": all_candidates,
        "limits": {
            "posthoc_exploratory_only": True,
            "inclusive_rank_is_not_p_value": True,
            "source_bat_plant_links_not_locally_verified": True,
            "plant_portfolios_share_species_and_seasonal_cycles": True,
            "seed_trap_counts_are_not_ripe_fruit_food_supply": True,
            "no_bat_activity_or_M3_prediction_evaluated": True,
            "no_independence_across_candidate_bats": True}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--primary-result", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        source = fetch_original(SEED_SOURCE_URL, SEED_BLOB_SHA)
        link = fetch_original(LINK_SOURCE_URL, LINK_BLOB_SHA)
        primary = json.loads(args.primary_result.read_text(encoding="utf-8"))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        payload = build_control(primary, source, link, manifest)
    except Exception as exc:
        payload = {"schema_version": 1, "status": "CC1_SIZE_MATCHED_SOURCE_OR_SCHEMA_STOP",
                   "error_type": type(exc).__name__, "error_code": str(exc)[:220]}
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(payload["status"], payload.get("error_code", ""), flush=True)
    return 0 if payload["status"] == "CC1_POSTHOC_SIZE_MATCHED_CONTROL_COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
