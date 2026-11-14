#!/usr/bin/env python3
"""Retrospective illustrative null baselines for the frozen Safari14 result.

Uses ONLY the original source-hash-pinned 39.5 KB aggregate JSON, not original
image/annotation records. This is a diagnostic of the weakness of the simple
'turnover > nestedness' criterion, NOT an ecological assembly hypothesis test,
parametric estimate, p-value, or new S14 field observation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import median

PINNED_INPUT_SHA256 = "f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
SEED = 20261114
DRAWS = 500
FREQUENCY_EXPONENTS = (0.0, 0.5, 1.0)
GROUPS = {
    "discovery": ("APN", "CDB", "ENO", "KAR", "KGA", "KRU", "LEC"),
    "validation": ("MAD", "MTZ", "PLN", "RUA", "TSW"),
}


def source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed_input(path: Path) -> dict:
    if source_digest(path) != PINNED_INPUT_SHA256:
        raise ValueError("frozen Safari14 aggregate SHA256 mismatch")
    doc = json.loads(path.read_text(encoding="utf-8"))
    labels = doc["quality"]["matched_wild_mammal_annotation_rows_by_label"]
    eligible = doc["results"]["eligible_projects"]
    if len(labels) != 38 or len(eligible) != 12:
        raise ValueError("frozen species-label pool or park support changed")
    if set(eligible) != set(GROUPS["discovery"] + GROUPS["validation"]):
        raise ValueError("original eligible park split changed")
    if not doc["results"]["predeclared_turnover_dominant_in_both_splits"]:
        raise ValueError("original empirical decision changed")
    for group in GROUPS:
        s = doc["results"]["beta_summary_by_project_partition"][group]
        if s["valid_resampling_draws"] != 500 or s["turnover_dominant_draws"] != 500:
            raise ValueError("original Safari14 camera-draw receipt changed")
    return doc


def beta_components(a: set, b: set) -> tuple[float, float, float]:
    if not a or not b:
        raise ValueError("nonempty sets required in null")
    shared = len(a & b)
    only_a, only_b = len(a-b), len(b-a)
    sor = (only_a + only_b)/(2*shared + only_a + only_b)
    sim = min(only_a, only_b)/(shared + min(only_a, only_b))
    sne = sor - sim
    if min(sor, sim, sne) < -1e-12 or not math.isclose(sor, sim+sne, abs_tol=1e-12):
        raise ValueError("Baselga decomposition failed")
    return sor, sim, max(0.0, sne)


def draw_without_replacement(weights: list[float], count: int, rng: random.Random) -> set[int]:
    """Exponential-race weighted sampling; uniform exactly when all weights equal."""
    if count < 1 or count > len(weights):
        raise ValueError("invalid richness target")
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError("species weights must be finite positive")
    priorities = [(-math.log(max(rng.random(), 1e-15))/w, i) for i,w in enumerate(weights)]
    priorities.sort()
    return {i for _,i in priorities[:count]}


def _quantiles(values: list[float]) -> tuple[float, float]:
    x = sorted(values)
    return x[max(0, math.floor(.05*(len(x)-1)))], x[min(len(x)-1, math.ceil(.95*(len(x)-1)))]


def model_group(richness: dict[str, int], weights: list[float], parks: tuple[str,...],
                rng: random.Random) -> dict[str,float]:
    sampled = {p:draw_without_replacement(weights, richness[p], rng) for p in parks}
    pair_values = [beta_components(sampled[a],sampled[b]) for a,b in combinations(parks,2)]
    return {
        "sor":median(v[0] for v in pair_values),
        "sim":median(v[1] for v in pair_values),
        "sne":median(v[2] for v in pair_values),
    }


def analyze(doc: dict, *, seed: int=SEED, draws: int=DRAWS) -> dict:
    # Camera-resampling medians are not integer. Round 19.5 to 20 by the
    # deterministic half-up rule: this is an ILLUSTRATIVE null, not the
    # actual S14 original camera-level richness distribution.
    parks = doc["results"]["project_summary"]
    richness = {
        p:math.floor(parks[p]["median_10_camera_detected_species"] + .5)
        for p in GROUPS["discovery"]+GROUPS["validation"]
    }
    label_counts = doc["quality"]["matched_wild_mammal_annotation_rows_by_label"]
    names = sorted(label_counts)
    global_image_weights = [label_counts[name] for name in names]
    if draws < 1:
        raise ValueError("at least one simulated draw is required")
    result = {}
    for idx, exponent in enumerate(FREQUENCY_EXPONENTS):
        # Global annotation-row counts are NOT true species occurrence
        # probabilities; their exponent is only a deliberately varied
        # sensitivity to unequal worldwide *image* label prevalence.
        weights = [n**exponent for n in global_image_weights]
        rng = random.Random(seed + idx*1009)
        samples = {group:{"sor":[],"sim":[],"sne":[],"dominance":0}
                   for group in GROUPS}
        for iteration in range(draws):
            for group, group_parks in GROUPS.items():
                q = model_group(richness, weights, group_parks, rng)
                for metric in ("sor","sim","sne"):
                    samples[group][metric].append(q[metric])
                samples[group]["dominance"] += int(q["sim"] > q["sne"])
        result[str(exponent)] = {}
        for group,q in samples.items():
            actual = doc["results"]["beta_summary_by_project_partition"][group]
            result[str(exponent)][group] = {
                "null_draws":draws,
                "median_null_beta_sim":median(q["sim"]),
                "null_beta_sim_5_to_95pct_draw_range":list(_quantiles(q["sim"])),
                "median_null_beta_sne":median(q["sne"]),
                "null_beta_sne_5_to_95pct_draw_range":list(_quantiles(q["sne"])),
                "null_draws_where_turnover_exceeds_nestedness":q["dominance"],
                "null_turnover_dominance_fraction":q["dominance"]/draws,
                "observed_original_beta_sim_median":actual["median_pair_sim"],
                "observed_original_beta_sne_median":actual["median_pair_sne"],
                "observed_minus_null_median_beta_sim":
                    actual["median_pair_sim"] - median(q["sim"]),
                "not_a_significance_comparison":True,
            }
    return {
        "schema_version":1,
        "status":"S14_POSTOUTCOME_STRUCTURAL_NULL_SENSITIVITY_NOT_ECOLOGICAL_INFERENCE",
        "source":{
            "original_empirical_run":42848095854,
            "original_zip_source_sha256":
                doc["source"]["original_zip_sha256"],
            "frozen_original_aggregate_sha256":PINNED_INPUT_SHA256,
            "biological_source_zip_reopened":False,
            "species_or_camera_ids_retrieved":False,
        },
        "settings":{
            "seed":seed,
            "draws_per_scenario":draws,
            "fixed_exponents":list(FREQUENCY_EXPONENTS),
            "label_pool_size":len(global_image_weights),
            "park_richness":richness,
            "richness_is_rounded_original_10_camera_median":True,
            "global_species_weight_proxy":"total source image annotation rows per recognized category, NOT independent camera incidence",
            "null_draws_are_illustrative_not_field_replicates":True,
            "null_sets_are_sampled_independently_by_park":True,
        },
        "null_scenarios":result,
        "interpretation":{
            "observed_partition_turnover_dominance_remains_true":True,
            "turnover_dominance_possible_under_random_species_assignment":True,
            "null_results_sensitive_to_global_label_frequency_weights":True,
            "nonrandom_assembly_proven":False,
            "environmental_filtering_or_competition_proven":False,
            "formal_null_significance_or_confidence_intervals":False,
            "true_occupancy_or_effort_calibrated":False,
            "original_E4_E5_E7_E7C_S14_findings_modified":False,
            "E5_G4_passed":False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-result",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result = analyze(observed_input(args.original_result))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "null_scenarios":{
            k:{g:{"null_turnover_dominance":v["null_turnover_dominance_fraction"],
                  "sim_median":v["median_null_beta_sim"],"sne_median":v["median_null_beta_sne"]}
               for g,v in scenario.items()}
            for k,scenario in result["null_scenarios"].items()
        },
    },sort_keys=True))


if __name__ == "__main__":
    main()
