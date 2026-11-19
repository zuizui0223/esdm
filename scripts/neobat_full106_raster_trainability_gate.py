"""NeoBat v2 fixed 106 plant training completeness after raster nodata (aggregate-only).

Reads prior original source-verified *per-plant-country aggregate source counts*,
not original GBIF locations, dataset keys, coordinates or source rasters.
No fitting, AUC model selection, or ecology promotion.
"""
from __future__ import annotations

import argparse,json,pathlib
from datetime import datetime,timezone
from collections import defaultdict

D=pathlib.Path("docs/replication/neobat")
SOURCE=D/"plant_106x17_source_effort_transfer.json"
GATE=D/"plant_dataset_matched_106x17_compact.json"
BAT=D/"bat_targetgroup_background_gate.json"
PARTNER=D/"v2_106plant_reference_input_gate.json"
DESIGN="docs/replication/NEOBAT_FULL106_RASTER_TRAINABILITY_FROZEN_20261119.md"
V2SHA="41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def analyse(prior,source_gate,bats,partners):
    if (prior.get("status")!="EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE"
        or prior.get("frozen_106_species_universe_sha256")!=V2SHA):
        raise ValueError("ORIGINAL_106x17_SOURCE_MODEL_OR_UNIVERSE_NOT_PINNED")
    if (source_gate.get("status")!="DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY"
        or source_gate["summary"]["source_matched_trainable_plant_country_pairs"]!=1802):
        raise ValueError("FROZEN_ORIGINAL_1802_SOURCE_QUANTITY_GATE_MISMATCH")
    if (bats.get("status")!="DOI_BAT_TARGETGROUP_BACKGROUND_INPUT_FEASIBILITY_ONLY"
        or partners.get("status")!="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY"):
        raise ValueError("FROZEN_BAT_PARTNER_SOURCE_GATES_MISSING")
    original=prior.get("plant_country_source_rank_results",[])
    batrows=bats.get("folds",[])
    partnerrows=partners.get("folds",[])
    if len(original)!=1802 or len(batrows)!=84 or len(partnerrows)!=84:
        raise ValueError("ORIGINAL_FULL_PLANT_OR_BAT_DENOMINATOR_CHANGED")
    plant_keys={(r["plant"],r["holdout_country"]) for r in original}
    species=sorted({x[0] for x in plant_keys})
    countries=sorted({x[1] for x in plant_keys})
    if len(species)!=106 or len(countries)!=17 or len(plant_keys)!=1802:
        raise ValueError("PLANT_COUNTRY_KEYS_DUPLICATE_OR_INCOMPLETE")
    bycountry=defaultdict(list)
    for r in original:
        countp=int(r["train_source_matched_focal_cells"])
        countbg=int(r["train_source_matched_target_background_cells"])
        if countp<0 or countbg<0:
            raise ValueError("INVALID_SOURCE_TRAINING_COUNTS")
        bycountry[r["holdout_country"]].append({
            "plant":r["plant"],
            "train_source_focal_cells_after_nodata":countp,
            "train_source_otherplant_bg_after_nodata":countbg,
            "trained_eligible":countp>=20 and countbg>=20
        })
    allcountries=[]
    complete=set()
    for country in countries:
        rr=bycountry[country]
        trainable=[x for x in rr if x["trained_eligible"]]
        fail=[x for x in rr if not x["trained_eligible"]]
        if len(rr)!=106 or len({x["plant"] for x in rr})!=106:
            raise ValueError("COUNTRY_PLANT_COHORT_NOT_106")
        if not fail:complete.add(country)
        allcountries.append({
            "country":country,
            "frozen_original_plant_species":106,
            "trainable_after_source_and_raster_nodata":len(trainable),
            "untrainable":len(fail),
            "all_106_trainable":not bool(fail),
            "untrainable_plant_names":[x["plant"] for x in fail],
            "train_positive_cells_lt20":sum(x["train_source_focal_cells_after_nodata"]<20 for x in fail),
            "train_background_cells_lt20":sum(x["train_source_otherplant_bg_after_nodata"]<20 for x in fail),
        })
    original_partner={(r["bat"],r["holdout_country"]):r for r in partnerrows}
    original_background={(r["bat"],r["holdout_country"]):r for r in batrows}
    if set(original_partner)!=set(original_background) or len(original_partner)!=84:
        raise ValueError("FROZEN_84_BAT_FOLDS_NOT_IDENTICAL")
    rows=[]
    for pair in sorted(original_partner):
        p=original_partner[pair]
        b=original_background[pair]
        ok=bool(p["v2_106_plant_input_qualified"] and b["quantity_qualified"])
        covered=pair[1] in complete
        rows.append({
            "bat":pair[0],"holdout_country":pair[1],
            "literature_partner_106_source_qualified":bool(p["v2_106_plant_input_qualified"]),
            "bat_targetgroup_background_source_qualified":bool(b["quantity_qualified"]),
            "joint_source_qualified_pre_raster":ok,
            "all_106_plant_crossfits_trainable_after_raster_nodata":covered,
            "full_v2_source_and_plant_training_ready":bool(ok and covered),
            "real_ecological_bat_M3_minus_M1_auc":None
        })
    if sum(x["joint_source_qualified_pre_raster"] for x in rows)!=79:
        raise ValueError("PREVIOUS_79_BAT_FOLDS_INTERSECTION_DRIFT")
    # All original 84 retained regardless of predictor lack and source AUC.
    n_ready=sum(x["full_v2_source_and_plant_training_ready"] for x in rows)
    return {
        "schema_version":1,
        "status":"FIXED106_PLANT_TRAINING_AFTER_RASTER_PREFIT_GATE",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "original_106x17_plant_country_pairs":1802,
        "all_84_original_bat_country_source_candidates_retained":True,
        "plant_universe_SHA256":V2SHA,
        "original_17_holdout_countries":len(countries),
        "countries_with_all_106_plant_model_training_ready":len(complete),
        "countries_with_some_untrainable_plant_models":len(countries)-len(complete),
        "source_input_79_bat_country_candidates_before_raster_gate":79,
        "full_fixed_106_plant_training_and_bat_source_qualified_pairs":n_ready,
        "stopped_bat_source_candidate_pairs_out_of_84":84-n_ready,
        "per_country":allcountries,
        "all_original_84_bat_folds":rows,
        "no_models_fitted_or_test_scores_inspected_in_this_gate":True,
        "not_true_plant_absences_or_resource_abundance":True,
        "no_M3_minus_M1_or_N1_ecological_effect":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=pathlib.Path,default=pathlib.Path(
        "docs/replication/neobat/full106_raster_trainability_gate.json"))
    args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=analyse(read(SOURCE),read(GATE),read(BAT),read(PARTNER))
    except Exception as exc:
        result={"schema_version":1,"status":"FIXED106_PLANT_TRAINING_GATE_STOP",
                "error_type":type(exc).__name__,
                "error_code":str(exc)[:230],"M3_minus_M1_auc":None}
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_FULL_106_PLANT_TRAINABLE",result["status"],flush=True)
    if "countries_with_all_106_plant_model_training_ready" in result:
        print("N_COUNTRIES",result["countries_with_all_106_plant_model_training_ready"])
        print("N_BAT_FOLDS",result["full_fixed_106_plant_training_and_bat_source_qualified_pairs"])
    return 0 if result["status"]=="FIXED106_PLANT_TRAINING_AFTER_RASTER_PREFIT_GATE" else 3


if __name__=="__main__":
    raise SystemExit(main())
