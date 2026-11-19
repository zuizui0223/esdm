"""NeoBat v3: fixed 35 globally source-disjoint plant trainability after raster screen.

Source-only count audit, 35 plants × 17 fixed original holdout countries.
Re-stream the original DOI-backed plant ZIP and pinned WorldClim sources;
reconstruct training botanical source intensity with *NO* datasetKey from
heldout country, never use heldout plant records to train models.
No plant or bat regression is fitted; no coordinates/source keys retained.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import tempfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts import neobat_plant_within_dataset_source_gate as source
from scripts import neobat_plant_global_dataset_embargo_gate as dataset
from scripts import neobat_CO_threeplant_crossdataset_transfer as cross
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_V3_SOURCE35_DATASET_DISJOINT_RASTER_TRAINABILITY_FROZEN_20261119.md"
PLANT_SHA="5f6ee54473b074b2b5329b1ddd9cc966e739f4f12b93db75154ce59a9f7b92ee"
N_ORIGINAL_PLANT_FOLDS=35*17
PASS="EXPLORATORY_V3_SOURCE35_DISJOINT_RASTER_TRAINABILITY_ONLY"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def freeze_inputs(v3,full):
    if v3.get("status")!="EXPLORATORY_V3_SOURCE_DISJOINT_35PLANT_FRUIT_PARTNER_GATE":
        raise RuntimeError("SOURCE35_FRUIT_PARTNER_GATE_MISSING")
    names=v3["source_disjoint_global35_plant_names"]
    holdouts=v3["original_country_holdouts"]
    sha=hashlib.sha256(("\n".join(names)+"\n").encode()).hexdigest()
    if (len(names)!=35 or sorted(set(names))!=names or
        len(holdouts)!=17 or len(set(holdouts))!=17 or
        sha!=PLANT_SHA or v3["source_disjoint_global35_names_sha256"]!=PLANT_SHA):
        raise RuntimeError("GLOBAL_SOURCE35_NAMES_OR_HOLDOUTS_DRIFT")
    if full.get("status")!=dataset.PASS_STATUS or len(full.get("plant_country_input_gates",[]))!=1802:
        raise RuntimeError("PREVIOUS_SOURCE_DISJOINT_1802_GATE_NOT_COMPLETE")
    bypair={(x["plant"],x["holdout_country"]):x
            for x in full["plant_country_input_gates"]}
    if len(bypair)!=1802:
        raise RuntimeError("PREVIOUS_1802_SOURCE_PAIR_DUPLICATION")
    for plant in names:
        for country in holdouts:
            original=bypair.get((plant,country))
            if not original or not original.get("train_quantity_eligible_after_global_dataset_embargo"):
                raise RuntimeError("GLOBAL_SOURCE35_PRE_RASTER_TRAINABILITY_STOP")
    if (len(v3.get("original_84_folds",[]))!=84 or
        v3["summary"]["qualified_with_bat_targetgroup_source_quantity"]!=63):
        raise RuntimeError("ORIGINAL_84_BAT_SOURCE_PAIRS_DRIFT")
    return names,holdouts,bypair


def screen(plant_cells,source_keys,source_index,rasters,names,holdouts,countries,prior):
    from pyproj import Transformer
    if len(countries)!=29 or len(holdouts)!=17 or len(names)!=35:
        raise RuntimeError("ORIGINAL_SOURCE_COUNTRY_OR_PLANT_DENOMINATOR_STOP")
    whole=pilot.country_cell_taxa(plant_cells)
    fixed=source.all_country_source_matches(names,plant_cells,countries)
    excluded_by={holdout:set(whole.get(holdout,{})) for holdout in holdouts}
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    env_cache={}
    records=[]
    for holdout in holdouts:
        blocked=source_keys.get(holdout,set())
        train_taxa=cross.unbanned_country_plant_taxa(source_index,blocked)
        excluded=excluded_by[holdout]
        for taxon in names:
            train=[]
            for country in countries:
                if country==holdout:
                    continue
                row,_=cross.training_source_cells(
                    taxon,country,plant_cells,source_index,train_taxa,
                    blocked,excluded)
                train.extend(row)
            test,_=cross.oldmatch.source_filtered_observation_cells(
                whole,fixed,taxon,holdout)
            original=prior[taxon,holdout]
            rawp=sum(int(x[1]) for x in train)
            rawb=len(train)-rawp
            if (rawp>original["train_focal_recorded_cells_disjoint_datasets"]
                or rawb>original["train_background_cells_disjoint_datasets"]):
                raise RuntimeError("POST_SELECTION_PRE_RASTER_SOURCE_CELL_COUNTS_INCREASED")
            trained,tnodata=pilot.dataframe_rows(train,rasters,xfm,env_cache)
            tested,h_nodata=pilot.dataframe_rows(test,rasters,xfm,env_cache)
            tp=sum(int(x[0]) for x in trained)
            tb=len(trained)-tp
            hp=sum(int(x[0]) for x in tested)
            hb=len(tested)-hp
            qualifies=tp>=20 and tb>=20
            testqual=hp>=5 and hb>=5
            records.append({
                "plant":taxon,
                "holdout_country":holdout,
                "pre_raster_source_disjoint_focal_cells":rawp,
                "pre_raster_source_disjoint_background_cells":rawb,
                "post_raster_source_disjoint_training_focal_cells":tp,
                "post_raster_source_disjoint_training_background_cells":tb,
                "post_raster_training_nodata_excluded_cells":tnodata,
                "post_raster_heldout_focal_recorded_cells":hp,
                "post_raster_heldout_background_recorded_cells":hb,
                "post_raster_heldout_nodata_excluded_cells":h_nodata,
                "train_quantity_qualified_after_raster":qualifies,
                "heldout_source_test_quantity_qualified_after_raster":testqual,
                "train_and_heldout_source_quantity_qualified_after_raster":
                    bool(qualifies and testqual),
                "same_GBIF_datasetKey_ever_in_holdout_excluded_from_all_training":True,
                "same_GBIF_dataset_is_not_independent_field_survey":True,
                "relative_species_suitability_fitted":False,
                "M3_minus_M1_bat_auc":None
            })
    if len(records)!=N_ORIGINAL_PLANT_FOLDS or len({
            (r["plant"],r["holdout_country"]) for r in records})!=N_ORIGINAL_PLANT_FOLDS:
        raise RuntimeError("SOURCE35_595_FOLD_ROSTER_MISSING_OR_DUPLICATED")
    return records


def report(records,v3,names,holdouts,source_rows,source_meta,raster_meta):
    bypair={(x["plant"],x["holdout_country"]):x for x in records}
    by_country=[]
    for cc in holdouts:
        subset=[bypair[name,cc] for name in names]
        count=sum(x["train_quantity_qualified_after_raster"] for x in subset)
        heldout=sum(x["train_and_heldout_source_quantity_qualified_after_raster"]
                    for x in subset)
        by_country.append({
            "holdout_country":cc,
            "original_fixed_source_disjoint_plant_species":35,
            "post_raster_trainable_source_disjoint_plants":count,
            "post_raster_train_and_test_source_quantity_qualified_plants":heldout,
            "complete_35_plant_predictor_trainability_source":count==35,
            "plant_training_shortfall_count":35-count
        })
    ready={x["holdout_country"]:x["complete_35_plant_predictor_trainability_source"]
           for x in by_country}
    prior_folds=v3["original_84_folds"]
    bat=[]
    for row in prior_folds:
        old=row["new35_and_bat_source_quantity_qualified"]
        cc=row["holdout_country"]
        bat.append({
          "bat":row["bat"],
          "holdout_country":cc,
          "pre_raster_35plant_literature_N1_bat_source_qualified":old,
          "all_fixed35_source_disjoint_plant_models_have_20plus_raster_cells":ready[cc],
          "new35_and_bat_source_and_raster_input_qualified":bool(old and ready[cc]),
          "real_bat_M3_minus_M1_auc":None
        })
    countrytrainable={x["holdout_country"] for x in by_country
                      if x["complete_35_plant_predictor_trainability_source"]}
    all17plants=sum(all(bypair[name,cc]["train_quantity_qualified_after_raster"]
                       for cc in holdouts) for name in names)
    return {
        "schema_version":1,
        "status":PASS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "original_bat_country_denominator":84,
        "original_35plant_country_denominator":N_ORIGINAL_PLANT_FOLDS,
        "original_fixed_source35_plant_names_SHA256":PLANT_SHA,
        "source_plant_DOI":EXPECTED["plant"]["doi"],
        "source_archive_sha256":source_meta["sha256"],
        "raster_archive_signatures":raster_meta,
        "source_dataset_keys_used_in_memory_only":True,
        "all_previous_source_disjoint_global35_folds_required":True,
        "no_bat_or_plant_model_fitted":True,
        "M3_minus_M1_bat_auc":None,
        "M3_minus_N1_bat_auc":None,
        "summary":{
           "fixed_35_plant_17_country_pairs":595,
           "source_disjoint35_post_raster_training_qualified_pairs":sum(
               x["train_quantity_qualified_after_raster"] for x in records),
           "source_disjoint35_post_raster_train_and_test_qualified_pairs":sum(
               x["train_and_heldout_source_quantity_qualified_after_raster"] for x in records),
           "fixed35_plants_raster_trainable_in_all17_holdouts":all17plants,
           "countries_with_all35_source_disjoint_post_raster_trainable":len(countrytrainable),
           "original84_bat_country_folds":84,
           "prior_fixed35_bat_background_literature_N1_qualified_folds":sum(
               x["pre_raster_35plant_literature_N1_bat_source_qualified"] for x in bat),
           "new_source_disjoint35_raster_and_bat_source_qualified_folds":sum(
               x["new35_and_bat_source_and_raster_input_qualified"] for x in bat),
           "source_only_not_actual_M3_M1_result":True
        },
        "per_country":by_country,
        "source_disjoint35_plant_country_folds":records,
        "original_84_bat_country_folds":bat,
        "raw_plant_GBIF_rows_or_cells_or_source_datasetIDs_saved":False
    }


def execute():
    v3=read(D/"v3_source_disjoint35_partner_gate.json")
    previous=read(D/"plant_106x17_global_source_embargo.json")
    names,holdouts,prior=freeze_inputs(v3,previous)
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    source_recs=verified_source(read(D/"gbif_download_submission.json"),
                                read(D/"gbif_download_doi_poll.json"))
    header=read(D/"gbif_archive_header_preflight.json")
    original_qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    with tempfile.TemporaryDirectory(prefix="neobat-global-source35-raster-") as temp:
        directory=pathlib.Path(temp)
        plantfile=directory/"original_plant.zip"
        orig=source_recs["plant"]
        if orig["doi"]!=EXPECTED["plant"]["doi"] or \
           orig["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
            raise RuntimeError("ORIGINAL_PLANT_DOI_SOURCE_CHANGED")
        signature=safe_archive(orig["url"],plantfile)
        if signature["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           signature["sha256"]!=header["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_PLANT_GBIF_ZIP_SHA_DRIFT")
        cells=strict_cell_records(plantfile,group="plant",
            source=header["files"]["plant"],accepted=accepted["plant"],
            expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,original_qc)
        source_keys,source_stats=dataset.source_embargo_from_archive(
            plantfile,header["files"]["plant"],EXPECTED["plant"]["n_records"])
        old_source_stats=previous["source_row_audit"]
        if (source_stats["source_dataset_country_counts"]!=old_source_stats["source_dataset_country_counts"]
            or source_stats["total_unique_original_dataset_keys_any_country"]!=1202):
            raise RuntimeError("FULL_ORIGINAL_DATASETKEY_COUNTRY_ROSTER_DRIFT")
        source_index=source.country_dataset_cells(cells)
        tiff_sources,raster_meta=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,tiff_sources)
            records=screen(cells,source_keys,source_index,rasters,names,holdouts,countries,prior)
    return report(records,v3,names,holdouts,source_stats,signature,raster_meta)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/v3_source35_raster_trainability.json")
    p.add_argument("--compact",default="build/neobat/v3_source35_raster_trainability_compact.json")
    args=p.parse_args();path=pathlib.Path(args.out);compact=pathlib.Path(args.compact)
    path.parent.mkdir(parents=True,exist_ok=True)
    compact.parent.mkdir(parents=True,exist_ok=True)
    try:result=execute()
    except Exception as exc:
        result={"schema_version":1,"status":"V3_SOURCE35_DISJOINT_RASTER_TRAINABILITY_STOP",
                "error_type":type(exc).__name__,
                "error_code":str(exc)[:220],
                "M3_minus_M1_bat_auc":None}
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    trimmed={k:v for k,v in result.items() if k!="source_disjoint35_plant_country_folds"}
    compact.write_text(json.dumps(trimmed,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_GLOBAL_SOURCE35_RASTER_GATE",result["status"],flush=True)
    if "summary" in result:
        print("SOURCE35_RASTER_SUMMARY",json.dumps(result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]==PASS else 3


if __name__=="__main__":
    raise SystemExit(main())
