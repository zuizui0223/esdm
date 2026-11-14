#!/usr/bin/env python3
"""S14-FM conditional camera-species-incidence null; all original biology fixed.

Single *post-outcome* source re-opening to recover eligible camera x mammal
binary incidence not present in published aggregate. Within each frozen park
partition, camera richness, species camera prevalence, park station totals,
and the original camera-subsampling selections are exactly preserved.

This is a conditional recorded-assemblage diagnostic, not an eSDM fit,
independent field replication, G4 qualification, a calibrated camera detector,
a formal p-value, or a tested ecological causation mechanism.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import median

from scripts.safari14_spatial_beta import (
    PINNED_ZIP_SHA256, DISCOVERY, VALIDATION, PROJECTS,
    RAREFACTION_CAMERAS, RNG_SEED, RAREFACTION_DRAWS,
    MIN_SEQUENCES_PER_CAMERA, TAXON_MIN_CAMERAS_WITH_RECORD,
    beta_components, load_camera_incidence,
)

ORIGINAL_JSON_SHA256 = "f9d263daa232651d9337f4d4125ae54ff34dcb248a91aef7ee7be75578cff6c7"
NULL_SEED = 20261114
BURNIN_PER_CAMERA = 30
BETWEEN_PER_CAMERA = 15
COMPARE_DRAWS = 500
MIN_POSITIVE_PAIRED_DRAWS = 475
NULL_SPLITS = {"discovery":DISCOVERY, "validation":VALIDATION}
SOURCE_COMPONENT_KEYS = ("sor", "sim", "sne")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def _median(xs):
    return median(xs) if xs else None


def _quantile_range(xs: list[float]) -> list[float] | None:
    if not xs:
        return None
    ordered = sorted(xs)
    return [ordered[max(0, math.floor(.05*(len(xs)-1)))],
            ordered[min(len(xs)-1, math.ceil(.95*(len(xs)-1)))]]


def label_set(rows, indices) -> set[str]:
    occurrences = Counter()
    for i in indices:
        for species in rows[i]:
            occurrences[species] += 1
    return {species for species,n in occurrences.items()
            if n >= TAXON_MIN_CAMERAS_WITH_RECORD}


def project_pair_components(park_sets: dict, projects: tuple[str,...]):
    paired = {}
    for a,b in combinations(projects,2):
        x = park_sets.get(a,set())
        y = park_sets.get(b,set())
        paired[(a,b)] = beta_components(x,y)
    return paired


def summary_for_group(pair_values: dict) -> dict:
    values = [v for v in pair_values.values() if v is not None]
    if not values:
        return {"median_sor":None,"median_sim":None,"median_sne":None,
                "pair_count":0,"turnover_dominates":None}
    return {
        "median_sor":median(v[0] for v in values),
        "median_sim":median(v[1] for v in values),
        "median_sne":median(v[2] for v in values),
        "pair_count":len(values),
        "turnover_dominates":median(v[1] for v in values)>median(v[2] for v in values),
    }


def camera_index_draws(cameras_by_project: dict, *, draws:int=COMPARE_DRAWS,
                       seed:int=RNG_SEED) -> list[dict[str,list[int]]]:
    eligible = [p for p in PROJECTS if len(cameras_by_project[p])>=RAREFACTION_CAMERAS]
    if eligible != list(DISCOVERY+tuple(p for p in VALIDATION
                                       if len(cameras_by_project[p])>=RAREFACTION_CAMERAS)):
        raise ValueError("inconsistent original eligible project order")
    rng = random.Random(seed)
    return [
        {p:rng.sample(range(len(cameras_by_project[p])),RAREFACTION_CAMERAS)
         for p in eligible}
        for _ in range(draws)
    ]


def original_camera_draws(cameras: dict, selections: list[dict]) -> dict:
    # Reproduce the ORIGINAL 500 camera-subsample statistics and all 66
    # eligible project-pair medians before generating a new null result.
    observed = {g:[] for g in ("discovery","validation","cross")}
    perpair = defaultdict(list)
    for draw in selections:
        sets = {
            park:label_set([labels for _,labels in cameras[park]], indices)
            for park,indices in draw.items()
        }
        for group,projects in (
            ("discovery",DISCOVERY),("validation",VALIDATION),
            ("cross",tuple(draw))
        ):
            if group=="cross":
                values = {
                    (a,b):beta_components(sets[a],sets[b])
                    for a in DISCOVERY for b in VALIDATION
                    if a in sets and b in sets
                }
            else:
                valid = tuple(p for p in projects if p in sets)
                values = project_pair_components(sets,valid)
            if group!="cross":
                for pair,value in values.items():
                    perpair[pair].append(value)
            observed[group].append(summary_for_group(values))
    return {"draws":observed, "park_pairs":perpair}


def verify_original_reconstruction(original: dict, check: dict, *, draws=COMPARE_DRAWS):
    if draws!=RAREFACTION_DRAWS:
        raise ValueError("exact reconstruction requires all 500 original draws")
    orig = original["results"]
    expected_parks = list(DISCOVERY)+[p for p in VALIDATION if
        orig["project_summary"][p]["eligible_cameras"]>=RAREFACTION_CAMERAS]
    # Supports and sample-eligibility must match the original ground truth.
    if expected_parks != orig["eligible_projects"]:
        raise ValueError("frozen original project eligibility mismatch")
    for group in ("discovery","validation","cross"):
        data = check["draws"][group]
        source = orig["beta_summary_by_project_partition"][group]
        if len(data) != source["valid_resampling_draws"]:
            raise ValueError("original camera-draw count mismatch")
        for short,name in (("sor","median_pair_sor"),
                           ("sim","median_pair_sim"),
                           ("sne","median_pair_sne")):
            values = [d["median_"+short] for d in data
                      if d["median_"+short] is not None]
            if not values or not math.isclose(
                median(values),source[name],abs_tol=1e-12,rel_tol=1e-12
            ):
                raise ValueError(f"original {group} {short} metric mismatch")
        num = sum(d["turnover_dominates"] is True for d in data)
        if num!=source["turnover_dominant_draws"]:
            raise ValueError(f"original {group} dominance draws mismatch")
        pairs = [d["pair_count"] for d in data]
        if not math.isclose(median(pairs),source["median_pair_count_per_draw"],abs_tol=1e-12):
            raise ValueError(f"original {group} pair support mismatch")
    original_pairs={
        (r["project_1"],r["project_2"]):r
        for r in orig["all_91_park_pair_summaries"]
        if r["eligible_both"]
    }
    for pair,data in check["park_pairs"].items():
        expected = original_pairs[pair]["median_sim"]
        values = [x[1] for x in data if x is not None]
        if not values or not math.isclose(median(values),expected,abs_tol=1e-12):
            raise ValueError(f"original per-pair {pair} beta_sim mismatch")
    return True


def margin_signature(rows: list[set[str]]) -> tuple[list[int],Counter]:
    return [len(r) for r in rows],Counter(species for r in rows for species in r)


def curveball(rows: list[set[str]], rng: random.Random) -> bool:
    """One two-camera trade, preserving every row and species column total."""
    n=len(rows)
    if n<2:
        return False
    a=rng.randrange(n)
    b=rng.randrange(n-1)
    if b>=a:
        b+=1
    common=rows[a]&rows[b]
    unique_a=rows[a]-common
    unique_b=rows[b]-common
    if not unique_a or not unique_b:
        return False
    pool=sorted(unique_a|unique_b)
    rng.shuffle(pool)
    rows[a]=common|set(pool[:len(unique_a)])
    rows[b]=common|set(pool[len(unique_a):])
    return True


def _run_trades(rows: list[set[str]], n: int, rng: random.Random) -> int:
    return sum(curveball(rows,rng) for _ in range(n))


def per_partition_null(cameras: dict, projects: tuple[str,...],
                       selections:list[dict],
                       observed:list[dict],
                       *, seed:int, between:int=BETWEEN_PER_CAMERA,
                       burn:int=BURNIN_PER_CAMERA) -> dict:
    rows = []
    park_indices = {}
    for p in projects:
        if p not in selections[0]:
            raise ValueError("partition contains unsupported source park")
        park_indices[p] = list(range(len(rows),len(rows)+len(cameras[p])))
        rows.extend(set(species) for _,species in cameras[p])
    n=len(rows)
    if n<2:
        raise ValueError("cannot trade one camera")
    original_margins=margin_signature(rows)
    rng=random.Random(seed)
    burned=_run_trades(rows,burn*n,rng)
    if margin_signature(rows)!=original_margins:
        raise ValueError("fixed camera/species incidence margins drift after burnin")
    accepted=0
    records=[]
    paired_by_project=defaultdict(list)
    null_pairwise=defaultdict(list)
    for i, sample in enumerate(selections):
        accepted+=_run_trades(rows,between*n,rng)
        if i%100==0 and margin_signature(rows)!=original_margins:
            raise ValueError("fixed camera/species incidence margins drift in null chain")
        sets = {
            p:label_set(rows,[park_indices[p][j] for j in sample[p]])
            for p in projects
        }
        values=project_pair_components(sets,projects)
        current=summary_for_group(values)
        old=observed[i]
        for pair,value in values.items():
            null_pairwise[pair].append(value)
        for pair,value in project_pair_components(
            {p:label_set([labels for _,labels in cameras[p]],sample[p]) for p in projects},
            projects
        ).items():
            paired_by_project[pair].append(value)
        valid=(current["median_sim"] is not None and old["median_sim"] is not None
               and current["pair_count"]==old["pair_count"]==len(projects)*(len(projects)-1)//2)
        records.append({
            "observed_median_sim":old["median_sim"],
            "null_median_sim":current["median_sim"],
            "observed_median_sne":old["median_sne"],
            "null_median_sne":current["median_sne"],
            "null_pair_count":current["pair_count"],
            "complete_and_paired":valid,
            "observed_excess_sim":old["median_sim"]-current["median_sim"]
                    if valid else None,
            "null_turnover_gt_nestedness":current["turnover_dominates"]
        })
    if margin_signature(rows)!=original_margins:
        raise ValueError("fixed camera/species incidence margins drift at end")
    matched=[r for r in records if r["complete_and_paired"]]
    differences=[r["observed_excess_sim"] for r in matched]
    paired_project_results=[]
    for a,b in combinations(projects,2):
        old=[z[1] for z in paired_by_project[a,b] if z is not None]
        null=[z[1] for z in null_pairwise[a,b] if z is not None]
        paired_project_results.append({
            "project_1":a,"project_2":b,
            "original_observed_sim_median":_median(old),
            "null_sim_median":_median(null),
            "median_sim_excess_vs_null":median(old)-median(null) if old and null else None,
            "null_pair_draws_estimable":len(null),
        })
    return {
        "source_camera_rows":n,
        "source_column_taxon_labels":len(original_margins[1]),
        "source_camera_label_incidence_entries":sum(original_margins[0]),
        "initial_burnin_trade_attempts":burn*n,
        "initial_burnin_accepted_trades":burned,
        "total_between_draw_trade_attempts":len(selections)*between*n,
        "total_between_draw_accepted_trades":accepted,
        "all_camera_row_sums_preserved":True,
        "all_partition_species_camera_incidence_marginals_preserved":True,
        "paired_draws":len(records),
        "fully_eligible_paired_draws":len(matched),
        "observed_gt_null_draw_count":sum(x>0 for x in differences),
        "fraction_paired_observed_gt_null":sum(x>0 for x in differences)/len(matched)
                                       if matched else None,
        "observed_median_beta_sim":_median([r["observed_median_sim"] for r in matched]),
        "null_median_beta_sim":_median([r["null_median_sim"] for r in matched]),
        "null_median_beta_sne":_median([r["null_median_sne"] for r in matched]),
        "null_turnover_gt_nestedness_draws":sum(r["null_turnover_gt_nestedness"] is True for r in records),
        "median_paired_beta_sim_excess":_median(differences),
        "paired_beta_sim_excess_5_to_95pct_descriptive_range":_quantile_range(differences),
        "all_within_partition_park_pair_summaries":paired_project_results,
        "met_fixed_475_of_500_descriptive_excess_criterion":(
            len(matched)==COMPARE_DRAWS
            and sum(x>0 for x in differences)>=MIN_POSITIVE_PAIRED_DRAWS
        ),
    }


def run(original_zip: Path, original_json: Path, *,
        draws:int=COMPARE_DRAWS, burn:int=BURNIN_PER_CAMERA,
        between:int=BETWEEN_PER_CAMERA) -> dict:
    if digest(original_json)!=ORIGINAL_JSON_SHA256:
        raise ValueError("original Safari14 one-shot result JSON digest mismatch")
    prior=json.loads(original_json.read_text(encoding="utf-8"))
    cameras,source=load_camera_incidence(original_zip,expected_sha256=PINNED_ZIP_SHA256)
    if source["source"]["zip_sha256"]!=prior["source"]["original_zip_sha256"]:
        raise ValueError("source ZIP digest mismatched original Safari14 result")
    if source["quality"]!=prior["quality"]:
        raise ValueError("full Safari14 source record QC drift")
    selections=camera_index_draws(cameras,draws=draws)
    observed=original_camera_draws(cameras,selections)
    reconciled=verify_original_reconstruction(prior,observed,draws=draws)
    partial={}
    for index,(group,projects) in enumerate(NULL_SPLITS.items()):
        group_parks=tuple(p for p in projects if len(cameras[p])>=RAREFACTION_CAMERAS)
        if len(group_parks)!=len(projects):
            raise ValueError("previously frozen eligible park split changed")
        partial[group]=per_partition_null(
            cameras,group_parks,selections,observed["draws"][group],
            seed=NULL_SEED+index,burn=burn,between=between
        )
    both=all(partial[group]["met_fixed_475_of_500_descriptive_excess_criterion"]
             for group in NULL_SPLITS)
    return {
        "schema_version":1,
        "status":"S14_POSTRESULT_CAMERA_SPECIES_FIXED_MARGIN_SENSITIVITY",
        "source":{
            "safari14_original_source_zip_sha256":PINNED_ZIP_SHA256,
            "safari14_original_empirical_run_id":42848095854,
            "safari14_original_result_sha256":ORIGINAL_JSON_SHA256,
            "original_empirical_500_draw_statistics_reproduced":reconciled,
            "all_source_QC_equal_original":True,
            "wildlife_photos_downloaded":False,
            "raw_cameras_images_sequences_exported":False,
        },
        "fixed_algorithm":{
            "station_count_per_park":RAREFACTION_CAMERAS,
            "taxon_positive_in_selected_cameras":TAXON_MIN_CAMERAS_WITH_RECORD,
            "permutation_iterations_per_partition":draws,
            "original_source_sample_seed":RNG_SEED,
            "null_seed_discovery":NULL_SEED,
            "null_seed_validation":NULL_SEED+1,
            "burnin_trade_proposals_per_camera":burn,
            "between_replicate_trade_proposals_per_camera":between,
            "row_sums": "each camera's distinct observed mammal labels",
            "column_sums":"each label's total cameras over the whole partition",
            "park_assignments_cameras_and_camera_count_preserved":True,
            "null_hypothesis":"camera label exchangeability across parks conditional on both margins within partition",
            "predeclared_descriptive_excess_rule":"observed beta_sim > fixed-margin null in at least 475/500 paired draws in BOTH partitions",
        },
        "per_partition":partial,
        "strong_descriptive_excess_in_both_partitions":both,
        "scientific_limits":{
            "post_result_exploratory_new_source_opening":True,
            "not_independent_field_replication":True,
            "null_MCMC_states_are_not_independent_ecological_replicates":True,
            "fixed_margin_chain_mixing_and_uniformity_unproven":True,
            "camera_detection_and_source_effort_unmeasured":True,
            "geographical_source_pool_and_habitat_crossability_unjustified":True,
            "no_formal_null_pvalue_or_interval":True,
            "nonrandom_biological_assembly_not_identified":True,
            "E4_E5_E7_E7C_original_results_unchanged":True,
            "E5_G4_passed":False,
        },
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--original-result",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=run(args.source_zip,args.original_result)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_reproduced":result["source"]["original_empirical_500_draw_statistics_reproduced"],
        "both_splits_excess":result["strong_descriptive_excess_in_both_partitions"],
        "groups":{
            group:{key:part[key] for key in (
                "source_camera_rows","source_column_taxon_labels",
                "source_camera_label_incidence_entries","fully_eligible_paired_draws",
                "observed_gt_null_draw_count","observed_median_beta_sim",
                "null_median_beta_sim","null_median_beta_sne",
                "null_turnover_gt_nestedness_draws",
                "median_paired_beta_sim_excess",
                "met_fixed_475_of_500_descriptive_excess_criterion"
            )} for group,part in result["per_partition"].items()
        }
    },sort_keys=True))


if __name__=="__main__":
    main()
