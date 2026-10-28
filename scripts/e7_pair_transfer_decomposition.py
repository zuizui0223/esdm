#!/usr/bin/env python3
"""Algebraic transfer of gradient and residual parts of frozen E7 pair shifts.

This reads only the already-audited 66-pair aggregate CSV, never original
Serengeti biological records. Descriptive and outcome-aware, not a model fit,
independent ecological replication, or an inferential estimate.
"""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path

from scripts.e7_relational_coherence import _gradient_fit, load_pinned_pair_table

COHORTS = ("discovery", "validation")
COMMON_PAIR_COUNT = 46
CONNECTED_SPECIES = 11


def dot(a, b):
    if len(a) != len(b):
        raise ValueError("vector length mismatch")
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def cosine(a, b):
    aa, bb = dot(a, a), dot(b, b)
    if aa <= 0 or bb <= 0:
        raise ValueError("cannot normalize zero energy")
    return dot(a, b) / math.sqrt(aa * bb)


def skill(test, forecast):
    base = dot(test, test)
    if base <= 0:
        raise ValueError("undefined zero-change baseline")
    errors = [v-p for v, p in zip(test, forecast, strict=True)]
    return 1 - dot(errors, errors)/base


def split_pair_vectors(rows):
    edges = [(r["species_1"], r["species_2"]) for r in rows]
    taxa = sorted({t for edge in edges for t in edge})
    out = {"edges":edges, "taxa":taxa}
    for period in COHORTS:
        observed = [float(r[f"{period}_log_dry_over_wet"]) for r in rows]
        fit = _gradient_fit(edges, observed, taxa)
        gradient = fit["predicted_pair_shifts"]
        residual = [v-g for v, g in zip(observed, gradient, strict=True)]
        if abs(dot(gradient, residual)) > 1e-9 * max(1, dot(observed, observed)):
            raise ValueError("gradient/residual decomposition not orthogonal")
        out[period] = {"observed":observed, "gradient":gradient, "residual":residual}
    for grad in (out["discovery"]["gradient"], out["validation"]["gradient"]):
        for res in (out["discovery"]["residual"], out["validation"]["residual"]):
            if abs(dot(grad, res)) > 1e-9 * max(1, dot(grad, grad), dot(res, res)):
                raise ValueError("cross-period orthogonality failed")
    return out


def _mh(sites, factors, pair, phase):
    num = den = 0.
    for key, taxa in sorted(sites.items()):
        a, b = taxa[pair[0]]
        c, d = taxa[pair[1]]
        if phase == "dry":
            x, y = factors[key][pair[0]], factors[key][pair[1]]
            a, b, c, d = x*a, x*b, y*c, y*d
        n = a+b+c+d
        num += a*d/n
        den += b*c/n
    if num <= 0 or den <= 0:
        raise ValueError("synthetic MH numerator/denominator nonpositive")
    return num/den


def noncollapsibility_counterexample():
    """Exact no-change diel odds at all sites, yet MH triangle fails closure."""
    sites = {
        0: {"A":(8,4), "B":(4,32), "C":(16,2)},
        1: {"A":(2,2), "B":(4,4), "C":(16,32)},
        2: {"A":(2,16), "B":(16,32), "C":(16,32)},
    }
    factors = {
        0: {"A":4, "B":16, "C":1},
        1: {"A":1, "B":16, "C":4},
        2: {"A":4, "B":1, "C":4},
    }
    for key, taxa in sites.items():
        for species, (night, day) in taxa.items():
            multiplier = factors[key][species]
            if night*(day*multiplier) != day*(night*multiplier):
                raise AssertionError("counterexample diel odds drift")
    shifts = {
        a+b:math.log(_mh(sites, factors, (a,b), "dry") /
                     _mh(sites, factors, (a,b), "wet"))
        for a,b in combinations("ABC", 2)
    }
    return {
        "identical_three_site_support_for_all_pairs":True,
        "all_species_have_identical_wet_dry_night_midday_odds_within_each_site":True,
        "seasonal_multipliers_scale_both_hours_equally_for_each_species":True,
        "synthetic_pair_log_shifts":shifts,
        "synthetic_triangle_closure_log_units":shifts["AB"]+shifts["BC"]-shifts["AC"],
        "explanation":"Nonzero aggregate cycle can occur without any within-site diel change or biological interaction",
    }


def analyze(rows, *, check_original=False):
    shared = [r for r in rows if all(
        r[f"{p}_status"] == "DESCRIPTIVE_ESTIMABLE" for p in COHORTS
    )]
    if check_original and len(shared) != COMMON_PAIR_COUNT:
        raise ValueError("original 46-pair support drift")
    x = split_pair_vectors(shared)
    taxa = x["taxa"]
    if check_original and len(taxa) != CONNECTED_SPECIES:
        raise ValueError("original common-support taxon count drift")
    discovery, validation = x["discovery"], x["validation"]
    d, v = discovery["observed"], validation["observed"]
    gd, gv = discovery["gradient"], validation["gradient"]
    rd, rv = discovery["residual"], validation["residual"]
    grad_dot, cycle_dot = dot(gd,gv), dot(rd,rv)
    total_dot = dot(d,v)
    if not math.isclose(total_dot, grad_dot+cycle_dot, rel_tol=1e-12, abs_tol=1e-10):
        raise ValueError("cross-period decomposition identity failed")
    leave_one = []
    for removed in taxa:
        reduced = [r for r in shared if removed not in (r["species_1"],r["species_2"])]
        q = split_pair_vectors(reduced)
        a,b = q["discovery"],q["validation"]
        g = dot(a["gradient"],b["gradient"])
        c = dot(a["residual"],b["residual"])
        leave_one.append({
            "excluded_taxon":removed, "retained_edges":len(reduced),
            "gradient_cross_dot":g, "residual_cross_dot":c,
            "gradient_cosine":cosine(a["gradient"],b["gradient"]),
            "residual_cosine":cosine(a["residual"],b["residual"]),
            "positive_gradient_negative_residual":g>0 and c<0,
        })
    fake = noncollapsibility_counterexample()
    if check_original and fake["synthetic_triangle_closure_log_units"] <= 1:
        raise ValueError("synthetic counterexample drift")
    return {
        "schema_version":1,
        "status":"E7_POSTRESULT_PAIR_GRADIENT_RESIDUAL_TRANSFER_AUDIT",
        "source":{
            "original_E7_empirical_run_id":39222089646,
            "frozen_pair_table_sha256":"688bf6ff6d5289be6f577583f30a753f460bc53b03ca9c5d207a60f50d51951b",
            "original_relational_result":"docs/replication/E7_RELATIONAL_COHERENCE_RESULT.json",
            "new_biological_records_read":False,
        },
        "shared_graph":{
            "pair_edges":len(shared), "connected_taxa":len(taxa),
            "independent_cycle_space_dimension":len(shared)-len(taxa)+1,
            "previous_triangles_are_dependent":104,
        },
        "cross_period":{
            "raw_pair_vector_cosine":cosine(d,v),
            "gradient_component_cosine":cosine(gd,gv),
            "residual_component_cosine":cosine(rd,rv),
            "raw_dot":total_dot,
            "gradient_dot":grad_dot,
            "residual_dot":cycle_dot,
            "cross_gradient_residual_terms_zero_by_projection":True,
            "historical_full_pairs_on_validation_skill_vs_zero":skill(v,d),
            "historical_gradient_on_validation_skill_vs_zero":skill(v,gd),
            "historical_gradient_on_validation_gradient_skill_vs_zero":skill(gv,gd),
            "historical_residual_on_validation_residual_skill_vs_zero":skill(rv,rd),
            "positive_gradient_negative_residual_leave_one_taxon_count":sum(
                r["positive_gradient_negative_residual"] for r in leave_one),
            "leave_one_taxon_exclusions":len(leave_one),
            "leave_one_taxon_sensitivity":leave_one,
        },
        "stationary_diel_synthetic_counterexample":fake,
        "interpretation_boundary":{
            "post_outcome_decomposition_not_independent_test":True,
            "noncollapsible_MH_and_variable_site_weighting_can_produce_cycle":True,
            "nonzero_cycle_proves_biological_interactions":False,
            "stable_biological_trait_established_by_positive_gradient_cosine":False,
            "out_of_period_skill_positive":False,
            "no_p_values_or_CIs":True,
            "pair_edges_not_independent_units":True,
            "E4_frozen_scores_unchanged":True,
            "E5_original_G4_passed":False,
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-table",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=analyze(load_pinned_pair_table(args.pair_table),check_original=True)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "raw_cosine":result["cross_period"]["raw_pair_vector_cosine"],
        "gradient_cosine":result["cross_period"]["gradient_component_cosine"],
        "residual_cosine":result["cross_period"]["residual_component_cosine"],
        "leave_one_taxon_count":result["cross_period"]["positive_gradient_negative_residual_leave_one_taxon_count"],
        "no_diel_change_cycle":result["stationary_diel_synthetic_counterexample"]["synthetic_triangle_closure_log_units"],
    },sort_keys=True))


if __name__=="__main__":
    main()
