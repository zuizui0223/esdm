"""Joint original GBIF dataset-key-disjoint + WorldClim raster input gate.

Fixed 35 plant names × 17 countries = 595 source+abiotic trainability rows.
Replays exact previous Colombia three-sentinel source-disjoint training-cell
denominators and the original 84 bat source-fold roster. No model fitting,
no per-cell coordinates, source dataset IDs or raster pixels saved.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import tempfile
from collections import defaultdict,Counter
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts import neobat_plant_within_dataset_source_gate as ds
from scripts import neobat_plant_global_dataset_embargo_gate as embargo
from scripts import neobat_CO_threeplant_crossdataset_transfer as CO
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_35_SOURCE_DISJOINT_RASTER_JOINT_GATE_FROZEN_20261119.md"
PASS="EXPLORATORY_FIXED35_JOINT_DISJOINT_DATASET_AND_RASTER_TRAINABILITY"
STOP="FIXED35_JOINT_SOURCE_AND_RASTER_INPUT_STOP"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def unbanned_plant_taxa_for_holdout(source_index,banned,holdout):
    """Country -> cell -> original observed plants, only from allowed sources."""
    matched=defaultdict(lambda:defaultdict(set))
    for country,by_dataset in source_index.items():
        if country==holdout:
            continue
        for dataset_key,cellmap in by_dataset.items():
            if dataset_key in banned:
                continue
            for cell,plants in cellmap.items():
                matched[country][cell].update(plants)
    return matched


def evaluate_cell_trainability(cells,source_index,allowed_taxa,plant,holdout,
                              countries,banned,excluded,rasters,xfm,cache):
    alltraining=[]
    raw_p=raw_bg=0
    for country in countries:
        if country==holdout:continue
        source_rows,_=CO.training_source_cells(
            plant,country,cells,source_index,allowed_taxa,banned,excluded)
        alltraining.extend(source_rows)
        raw_p+=sum(int(x[1]) for x in source_rows)
        raw_bg+=sum(not x[1] for x in source_rows)
    valid,missing=pilot.dataframe_rows(alltraining,rasters,xfm,cache)
    np=sum(int(x[0]) for x in valid)
    nb=len(valid)-np
    if (np>raw_p or nb>raw_bg or raw_p+raw_bg!=len(alltraining) or
        len(alltraining)-len(valid)!=missing):
        raise RuntimeError("RASTER_OR_SOURCE_CLASS_DENOMINATOR_CONTRADICTION")
    return {
       "train_raw_positive_source_recorded_cells":raw_p,
       "train_raw_targetgroup_background_cells":raw_bg,
       "train_raster_valid_focal_recorded_cells":np,
       "train_raster_valid_targetgroup_background_cells":nb,
       "training_source_abiotic_nodata_excluded_cells":missing,
       "complete_train_20plus_each_class":np>=20 and nb>=20,
       "no_true_plant_absence":True
    }


def audit(cells,sourcekeys,selected,holdouts,countries,source35,source1802,
          prior_CO,rasters):
    from pyproj import Transformer
    if len(selected)!=35 or len(holdouts)!=17 or len(countries)!=29:
        raise ValueError("SOURCE35_OR_COUNTRY_UNIVERSE_CHANGED")
    pre35=source35.get("original_84_bat_country_folds")
    if source35.get("status")!="EXPLORATORY_FIXED35_BAT_FRUITLINK_SOURCE_AND_N1_FEASIBILITY_ONLY" or \
       not isinstance(pre35,list) or len(pre35)!=84:
        raise RuntimeError("PRIOR_SOURCE35_ORIGINAL_BAT_FOLDS_NOT_VERIFIED")
    prev=source1802.get("plant_country_input_gates")
    if source1802.get("status")!=embargo.PASS_STATUS or \
       not isinstance(prev,list) or len(prev)!=1802:
        raise RuntimeError("PREVIOUS_DISJOINT_1802_SOURCE_GATE_NOT_VERIFIED")
    prior_map={(x["plant"],x["holdout_country"]):x for x in prev}
    if len(prior_map)!=1802:
        raise RuntimeError("PREVIOUS_DISJOINT_1802_KEYS_NOT_UNIQUE")
    prior_CO_map={r["plant"]:r for r in prior_CO.get("plants",[])}
    if prior_CO.get("status")!=CO.PASS or set(prior_CO_map)!=set(pilot.SENTINELS):
        raise RuntimeError("PREVIOUS_CO_THREE_SENTINEL_DISJOINT_SOURCE_NOT_VERIFIED")
    full_country_cells=defaultdict(set)
    for (_,country),mapping in cells.items():
        full_country_cells[country].update(mapping)
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    # Build the 255-plant source->cell index ONCE; rerendering this index
    # per 35×17 fold would be a large avoidable memory/CPU penalty.
    source_index=ds.country_dataset_cells(cells)
    cache={}
    results=[]
    countries_report=[]
    for holdout in holdouts:
        banned=set(sourcekeys[holdout])
        allowed_taxa=unbanned_plant_taxa_for_holdout(
            source_index=source_index,banned=banned,holdout=holdout)
        excluded=set(full_country_cells[holdout])
        ready=0
        for name in selected:
            a=evaluate_cell_trainability(
                cells,source_index,allowed_taxa,name,holdout,
                countries,banned,excluded,rasters,xfm,cache)
            old=prior_map[name,holdout]
            if not old["train_quantity_eligible_after_global_dataset_embargo"]:
                raise RuntimeError("SELECTED35_PREVIOUS_SOURCE_TRAINABILITY_FALSE")
            if (a["train_raw_positive_source_recorded_cells"]>
                    old["train_focal_recorded_cells_disjoint_datasets"] or
                a["train_raw_targetgroup_background_cells"]>
                    old["train_background_cells_disjoint_datasets"]):
                raise RuntimeError("SOURCE35_ORIGINAL_PRE_ABIOTIC_COUNTS_NOT_MONOTONE")
            if holdout=="CO" and name in prior_CO_map:
                original=prior_CO_map[name]
                if (a["train_raster_valid_focal_recorded_cells"]!=
                        original["training_focal_recorded_cells_source_disjoint"] or
                    a["train_raster_valid_targetgroup_background_cells"]!=
                        original["training_background_cells_source_disjoint"] or
                    a["training_source_abiotic_nodata_excluded_cells"]!=
                        original["training_raster_nodata_excluded_cells"]):
                    raise RuntimeError("PREVIOUS_CO_THREE_SOURCE_RASTER_TRAINING_REPLAY_DRIFT_"+name)
            ready+=int(a["complete_train_20plus_each_class"])
            results.append({
                "plant":name,"holdout_country":holdout,
                **a,
                "source_key_embargoed_raster_preprocessing_consistent":True
            })
        countries_report.append({
            "holdout_country":holdout,
            "original_fixed_global35_plants":35,
            "joint_source_disjoint_raster_trainable_plants":ready,
            "joint_source_disjoint_raster_untrainable_plants":35-ready,
            "all35_joint_source_and_raster_training_input_qualified":ready==35,
            "source_country_original_dataset_keys_embargoed":len(banned)
        })
    if len(results)!=595 or len(countries_report)!=17:
        raise RuntimeError("ORIGINAL_FIXED_595_PLANT_COUNTRY_SOURCE_RASTER_MISSING")
    country_ready={x["holdout_country"]:x[
        "all35_joint_source_and_raster_training_input_qualified"]
        for x in countries_report}
    folds=[{
        "bat":r["bat"],"holdout_country":r["holdout_country"],
        "source35_literature_N1_bat_background_qualified":
            r["selected_35_joint_bat_background_and_link_N1_source_qualified"],
        "full35_original_plant_crossfits_joint_source_raster_training_qualified":
            country_ready[r["holdout_country"]],
        "joint_all_fixed35_plant_training_and_bat_source_inputs_possible":bool(
            r["selected_35_joint_bat_background_and_link_N1_source_qualified"] and
            country_ready[r["holdout_country"]]),
        "bat_M3_minus_M1_auc":None
    } for r in pre35]
    if len(folds)!=84:
        raise RuntimeError("ALL_ORIGINAL_84_BAT_FOLDS_NOT_RETAINED")
    source_qualified=sum(r[
        "selected_35_joint_bat_background_and_link_N1_source_qualified"]
        for r in pre35)
    actual=sum(r["joint_all_fixed35_plant_training_and_bat_source_inputs_possible"]
               for r in folds)
    if source_qualified!=63 or actual>source_qualified:
        raise RuntimeError("SOURCE35_SOURCE_ROSTER_MONOTONICITY_VIOLATED")
    distinct_bats={r["bat"] for r in folds
                   if r["joint_all_fixed35_plant_training_and_bat_source_inputs_possible"]}
    distinct_countries={r["holdout_country"] for r in folds
                        if r["joint_all_fixed35_plant_training_and_bat_source_inputs_possible"]}
    return {
        "schema_version":1,
        "status":PASS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "global35_original_species_SHA256":
            source35["source35_fixed_plant_names_sha256"],
        "all_original_global35_names_unchanged":True,
        "original_595_plant_country_pairs_accounted":True,
        "original_84_bat_folds_accounted":True,
        "source_data_set_ids_and_cell_identifiers_used_only_in_memory":True,
        "no_plant_or_bat_sdm_fitted":True,
        "M3_minus_M1_bat_auc":None,
        "M3_minus_N1_bat_auc":None,
        "summary":{
            "original_fixed35_plant_country_pairs":595,
            "joint_source_disjoint_and_raster_valid_trainable_pairs":sum(
                r["complete_train_20plus_each_class"] for r in results),
            "joint_source_disjoint_and_raster_valid_stopped_pairs":sum(
                not r["complete_train_20plus_each_class"] for r in results),
            "countries_with_all35_joint_source_raster_trainable":sum(
                x["all35_joint_source_and_raster_training_input_qualified"]
                for x in countries_report),
            "original_source_only_35_partner_and_N1_and_bat_background_folds":63,
            "joint_source_raster_plus_bat_literature_N1_input_folds":actual,
            "joint_bat_species_represented":len(distinct_bats),
            "joint_bat_countries_represented":len(distinct_countries),
            "no_fitted_plant_suitability_maps_or_ecological_bat_AUC":True
        },
        "per_country":countries_report,
        "plant_country_source_raster_training_gate":results,
        "all_84_bat_folds":folds
    }


def execute():
    source35=read(D/"source35_bat_literature_N1_input_gate.json")
    if source35.get("status")!="EXPLORATORY_FIXED35_BAT_FRUITLINK_SOURCE_AND_N1_FEASIBILITY_ONLY" or \
       len(source35.get("source35_fixed_plant_names",[]))!=35:
        raise RuntimeError("FIXED_SOURCE35_AUTHOR_GATE_UNVERIFIED")
    selected=source35["source35_fixed_plant_names"]
    source1802=read(D/"plant_106x17_global_source_embargo.json")
    prior_CO=read(D/"CO_three_plant_disjoint_source_AUC.json")
    _,holdouts=ds.fixed_names_and_countries()
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    originals=verified_source(read(D/"gbif_download_submission.json"),
                              read(D/"gbif_download_doi_poll.json"))
    archive_header=read(D/"gbif_archive_header_preflight.json")
    source_qc=read(D/"gbif_full_source_qc.json")
    name_mapping=name_map(read(D/"gbif_search_preflight.json"),
                          read(D/"plant_search_preflight.json"))
    with tempfile.TemporaryDirectory(prefix="neobat-joint35-source-raster-") as tmp:
        directory=pathlib.Path(tmp)
        filename=directory/"plant_original.zip"
        original=originals["plant"]
        if original["doi"]!=EXPECTED["plant"]["doi"] or \
           original["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
            raise RuntimeError("ORIGINAL_PLANT_DOI_ROW_DENOMINATOR_DRIFT")
        info=safe_archive(original["url"],filename)
        if info["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           info["sha256"]!=archive_header["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_PLANT_ZIP_SHA_DRIFT")
        cells=strict_cell_records(filename,group="plant",
            source=archive_header["files"]["plant"],
            accepted=name_mapping["plant"],expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,source_qc)
        keys,metadata=embargo.source_embargo_from_archive(
            filename,archive_header["files"]["plant"],EXPECTED["plant"]["n_records"])
        originalzip,climate=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,originalzip)
            result=audit(cells,keys,selected,holdouts,countries,
                         source35,source1802,prior_CO,rasters)
    result["original_plant_DOI"]=EXPECTED["plant"]["doi"]
    result["original_plant_ZIP_SHA256"]=info["sha256"]
    result["original_climate_ZIP_SHA256"]=climate["climate_zip_sha256"]
    result["original_elevation_ZIP_SHA256"]=climate["elevation_zip_sha256"]
    result["prior_CO_fixed_three_training_counts_replayed_exactly"]=True
    result["raw_source_dataset_keys_or_coordinates_or_pixels_persisted"]=False
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/joint35_source_raster_trainability.json")
    p.add_argument("--compact",default="build/neobat/joint35_source_raster_trainability_compact.json")
    a=p.parse_args()
    full=pathlib.Path(a.out); compact=pathlib.Path(a.compact)
    full.parent.mkdir(parents=True,exist_ok=True);compact.parent.mkdir(parents=True,exist_ok=True)
    try:result=execute()
    except Exception as exc:
        result={
           "schema_version":1,"status":STOP,
           "error_type":type(exc).__name__,"error_code":str(exc)[:220],
           "M3_minus_M1_bat_auc":None
        }
    full.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    compact.write_text(json.dumps({
        k:v for k,v in result.items()
        if k not in ("plant_country_source_raster_training_gate","all_84_bat_folds")
    },indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_FIXED35_JOINT_SOURCE_RASTER",result["status"],flush=True)
    if "summary" in result:
        print("NEOBAT_FIXED35_JOINT_SUMMARY",json.dumps(result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]==PASS else 3


if __name__=="__main__":
    raise SystemExit(main())
