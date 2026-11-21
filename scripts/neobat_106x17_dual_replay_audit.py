"""Reconcile two pre-existing fixed 106x17 plant source-rank aggregate results.

No original observations, coordinates, raster pixels, dataset keys, or
new ecological model fitting. Fail closed on any per-fold discrepancy.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from datetime import datetime,timezone

PIN_A="4cf7c601473f70daa9f9ff5cbf7b30c3c0abb41a"
PIN_B="e940be5799bb98c59f708cb6da454f11d1f24b30"
A_BLOB="3389fda966cb3c7566ff5d249396fed725f16a05"
B_BLOB="7a84042d25f4809e5169da6881242b33170be7d0"
DESIGN="docs/replication/NEOBAT_106x17_DUAL_SOURCE_MODEL_REPLAY_FROZEN_20261119.md"
A_STATUS="EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE"
B_STATUS="EXPLORATORY_106x17_SOURCE_MATCHED_INTENSITY_DIAGNOSTIC_COMPLETE"
V2_SHA="41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def value_equal(a,b,limit=1e-10):
    if a is None or b is None:
        return a is None and b is None
    try:
        fa=float(a);fb=float(b)
    except (TypeError,ValueError):
        return a==b
    return math.isfinite(fa) and math.isfinite(fb) and abs(fa-fb)<=limit


def compare(a,b):
    if a.get("status")!=A_STATUS or b.get("status")!=B_STATUS:
        raise RuntimeError("TWO_COMPLETED_SOURCE_MODELS_REQUIRED")
    if a.get("original_plant_GBIF_DOI")!=b.get("GBIF_plant_original_DOI") or \
       a.get("original_plant_ZIP_SHA256")!=b.get("GBIF_plant_original_zip_sha256") or \
       a.get("frozen_106_species_universe_sha256")!=b.get("frozen_106_plant_universe_sha256"):
        raise RuntimeError("SOURCE_DOI_HASH_OR_UNIVERSE_NOT_IDENTICAL")
    climate_a=a.get("WorldClim_climate_ZIP_SHA256")
    elev_a=a.get("WorldClim_elevation_ZIP_SHA256")
    raster_b=b.get("raster_source") or {}
    if (not climate_a or not elev_a or
        climate_a!=raster_b.get("climate_zip_sha256") or
        elev_a!=raster_b.get("elevation_zip_sha256")):
        raise RuntimeError("ORIGINAL_WORLDCLIM_CLIMATE_OR_ELEVATION_HASH_DIFFERENCE")
    if a.get("frozen_106_species_universe_sha256")!=V2_SHA or \
       not a.get("previous_3sentinel_CO_AUCs_exactly_replayed") or \
       not b.get("original_3_sentinel_CO_model_AUC_and_cells_exactly_replayed"):
        raise RuntimeError("PINNED_PLANT_COHORT_OR_CO_SENTINEL_REPLAY_STOP")
    arr_a=a.get("plant_country_source_rank_results",[])
    arr_b=b.get("all_1802_fold_rows",[])
    if len(arr_a)!=1802 or len(arr_b)!=1802:
        raise RuntimeError("TWO_FULL_1802_COHORTS_REQUIRED")
    key=lambda r:(r["plant"],r["holdout_country"])
    if len(set(map(key,arr_a)))!=1802 or len(set(map(key,arr_b)))!=1802:
        raise RuntimeError("DUPLICATE_PLANT_COUNTRY_KEY")
    map_a={key(x):x for x in arr_a}
    map_b={key(x):x for x in arr_b}
    if set(map_a)!=set(map_b):
        raise RuntimeError("IMPL_A_B_COUNTRY_OR_PLANT_KEY_DIFFERENCE")
    status_mismatch=[]
    denominator_mismatch=[]
    score_mismatch=[]
    maxdiff=0.0
    max_exact_1e12=0
    fit_count=0
    for k in sorted(map_a):
        x,y=map_a[k],map_b[k]
        fit_a=x["status"]=="EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC"
        fit_b=y["status"]=="EXPLORATORY_SOURCE_MATCHED_RANK_AUC"
        if fit_a!=fit_b:status_mismatch.append(k)
        if fit_a:fit_count+=1
        for col_a,col_b in (
            ("train_source_matched_focal_cells","train_positive_recorded_cells"),
            ("train_source_matched_target_background_cells","train_pseudo_background_cells"),
            ("heldout_source_matched_focal_cells","heldout_positive_recorded_cells"),
            ("heldout_source_matched_target_background_cells","heldout_pseudo_background_cells"),
            ("heldout_abiotic_nodata_cell_exclusions","heldout_raster_nodata_removed_cells"),
        ):
            if x[col_a]!=y[col_b]:
                denominator_mismatch.append((k,col_a))
        for col_a,col_b in (
            ("AUC_abiotic_only","AUC_abiotic_only"),
            ("AUC_source_intensity_only","AUC_effort_only"),
            ("AUC_abiotic_plus_source_intensity","AUC_abiotic_plus_otherplant_effort"),
            ("delta_AUC_abiotic_added_to_source_intensity","delta_added_abiotic_beyond_source_intensity"),
        ):
            av,bv=x[col_a],y[col_b]
            if not value_equal(av,bv):
                score_mismatch.append((k,col_a))
            elif av is not None and bv is not None:
                diff=abs(float(av)-float(bv))
                maxdiff=max(maxdiff,diff)
                if diff>1e-12:max_exact_1e12+=1
        cond=y["exact_intensity_conditional_auc"]
        bv=cond["auc"] if cond else None
        bv_cov=cond["comparable_pair_fraction"] if cond else None
        for col_a,bv0 in (
            ("exact_same_intensity_heldout_AUC",bv),
            ("exact_same_intensity_comparable_pair_fraction",bv_cov)
        ):
            av=x[col_a]
            if not value_equal(av,bv0):score_mismatch.append((k,col_a))
            elif av is not None:
                diff=abs(float(av)-float(bv0))
                maxdiff=max(maxdiff,diff)
                if diff>1e-12:max_exact_1e12+=1
    if fit_count!=647:
        raise RuntimeError("FITTED_DENOMINATOR_NOT_647")
    if status_mismatch or denominator_mismatch or score_mismatch:
        raise RuntimeError(
            "CROSS_IMPLEMENTATION_DISCREPANCY_STATUS_"+str(len(status_mismatch))+
            "_DENOM_"+str(len(denominator_mismatch))+
            "_SCORE_"+str(len(score_mismatch))
        )
    sa,sb=a["summary"],b["summary"]
    if (sa["source_matched_plant_country_rank_AUC_measured"]!=fit_count or
        sb["source_and_model_fit_eligible"]!=fit_count or
        not value_equal(sa["per_country_equal_delta_AUC_mean"],
                        sb["equal_country_mean_added_abiotic_delta"])):
        raise RuntimeError("AGGREGATED_SOURCE_RANK_RESULT_MISMATCH")
    return {
        "schema_version":1,
        "status":"FULL_1802_FOLD_TWO_IMPLEMENTATION_AGGREGATE_REPLAY_MATCH",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "design":DESIGN,
        "implementation_A_commit":PIN_A,
        "implementation_B_commit":PIN_B,
        "implementation_A_blob_sha1":A_BLOB,
        "implementation_B_blob_sha1":B_BLOB,
        "original_fixed_plant_country_pairs":1802,
        "same_source_rank_fitted_pairs":647,
        "both_source_or_quantity_STOP_pairs":1155,
        "status_pair_mismatches":len(status_mismatch),
        "source_denominator_pair_mismatches":len(denominator_mismatch),
        "auc_or_conditional_pair_mismatches":len(score_mismatch),
        "max_absolute_numeric_difference":maxdiff,
        "numeric_score_fields_differing_more_than_1e_minus12":max_exact_1e12,
        "equal_country_mean_abiotic_added_AUC":sa["per_country_equal_delta_AUC_mean"],
        "same_original_GBIF_and_worldclim_and_utility_code_not_external_replication":True,
        "no_bat_M3_minus_M1_or_N1_effect_estimated":True,
        "no_raw_source_rows_or_coordinates_opened_or_exported":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--a",type=pathlib.Path,required=True)
    p.add_argument("--b",type=pathlib.Path,required=True)
    p.add_argument("--out",type=pathlib.Path,default=pathlib.Path(
        "build/neobat/two_implementation_replay.json"))
    args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=compare(load(args.a),load(args.b))
    except Exception as exc:
        result={
            "schema_version":1,"status":"TWO_IMPLEMENTATION_REPLAY_DISCREPANCY_STOP",
            "error_type":type(exc).__name__,
            "error_code":str(exc)[:250],
            "bat_M3_minus_M1_auc":None
        }
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_TWO_IMPLEMENTATIONS",result["status"])
    return 0 if result["status"]=="FULL_1802_FOLD_TWO_IMPLEMENTATION_AGGREGATE_REPLAY_MATCH" else 3


if __name__=="__main__":
    raise SystemExit(main())
