"""Source-disjoint Colombia 3-plant test with original test rows held constant.

Post-hoc plant GBIF source-robustness only. Train excludes ALL datasetKeys
ever seen in original Colombia botanical records; *training* other-species
intensity is reconstructed only from nonembargoed datasets. Original
Colombia source-matched test population and old AUCs are replayed exactly.
No bat model, original coordinates, per-cell scores or keys emitted.
"""
from __future__ import annotations
import argparse
import json
import math
import pathlib
import tempfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime, timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts import neobat_plant_effort_confounding_diagnostic as diag
from scripts import neobat_plant_source_matched_co_pilot as oldmatch
from scripts import neobat_plant_within_dataset_source_gate as source
from scripts import neobat_plant_global_dataset_embargo_gate as embargo
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_CO_3PLANT_CROSS_DATASET_TRANSFER_FROZEN_20261119.md"
PASS="EXPLORATORY_POSTHOC_CO_3PLANT_DISJOINT_SOURCE_TRANSFER"
STOP="CO_THREE_PLANT_DISJOINT_SOURCE_TRANSFER_STOP"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def unbanned_country_plant_taxa(per_country_dataset,embargo_keys):
    """Only other plants observed by source datasets absent from heldout."""
    out=defaultdict(lambda:defaultdict(set))
    for country,by_dataset in per_country_dataset.items():
        if country==pilot.HOLDOUT:
            continue
        for key,cellmap in by_dataset.items():
            if key in embargo_keys:continue
            for cell,taxa in cellmap.items():
                out[country][cell].update(taxa)
    return out


def training_source_cells(plant,country,cell_index,source_index,other_plant_taxa,
                          forbidden_keys,heldout_cells):
    p,b,n_datasets=embargo.source_matched_country_excluding(
        plant,country,cell_index,source_index,forbidden_keys)
    observations=pilot.make_labeled_cells(
        other_plant_taxa,plant,country,excluded_cells=heldout_cells)
    filtered=[
        r for r in observations
        if (r[1]==1 and r[0] in p) or
           (r[1]==0 and r[0] in b)
    ]
    if len(filtered)!=len({x[0] for x in filtered}):
        raise RuntimeError("DUPLICATE_TRAINING_CELL_IN_COUNTRY")
    if any(x[0] in heldout_cells for x in filtered):
        raise RuntimeError("HELDOUT_COUNTRY_CELL_USED_IN_TRAINING")
    return filtered,n_datasets


def replay_original_source_matched(cells,rasters,countries):
    actual=oldmatch.fit_sentinels(cells,rasters,countries)
    previous=read(D/"plant_CO_source_datasetmatched_pilot.json")
    if previous.get("status")!="EXPLORATORY_ORIGINAL_DATASETMATCHED_3PLANT_CO_MODEL_COMPLETE":
        raise RuntimeError("ORIGINAL_MATCHED_CO_RESULT_NOT_COMPLETE")
    a={x["plant"]:x for x in actual}
    b={x["plant"]:x for x in previous["plants"]}
    if set(a)!=set(pilot.SENTINELS) or set(b)!=set(pilot.SENTINELS):
        raise RuntimeError("FROZEN_THREE_SENTINELS_CHANGED")
    for name in pilot.SENTINELS:
        for k in (
          "train_source_matched_plant_recorded_cells",
          "train_source_matched_background_cells",
          "test_source_matched_plant_recorded_cells",
          "test_source_matched_background_cells",
          "train_raster_nodata_excluded_cells",
          "test_raster_nodata_excluded_cells",
          "status"
        ):
            if a[name][k]!=b[name][k]:
                raise RuntimeError("ORIGINAL_SOURCE_MATCHED_COUNTS_CHANGED_"+name)
        for k in ("AUC_abiotic_only","AUC_effort_only",
                  "AUC_abiotic_plus_otherplant_effort",
                  "increment_AUC_environment_beyond_effort_only"):
            if not math.isclose(
                a[name]["diagnostics"][k],b[name]["diagnostics"][k],
                rel_tol=0,abs_tol=1e-12):
                raise RuntimeError("ORIGINAL_SOURCE_MATCHED_AUC_CHANGED_"+name)
    return b


def evaluate(cells,source_index,forbidden,rasters,countries,old):
    from pyproj import Transformer
    test_taxa=pilot.country_cell_taxa(cells)
    original_matches=source.all_country_source_matches(
        pilot.SENTINELS,cells,countries)
    eligible_training_taxa=unbanned_country_plant_taxa(source_index,forbidden)
    heldout_cells=set(test_taxa[pilot.HOLDOUT])
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    cache={}
    results=[]
    for species in pilot.SENTINELS:
        original=old[species]
        test_raw,n_test_source_keys=oldmatch.source_filtered_observation_cells(
            test_taxa,original_matches,species,pilot.HOLDOUT)
        train_raw=[]
        train_source_contexts=0
        for country in countries:
            if country==pilot.HOLDOUT:continue
            cohort,n_sources=training_source_cells(
                species,country,cells,source_index,eligible_training_taxa,
                forbidden,heldout_cells)
            train_raw.extend(cohort)
            train_source_contexts+=n_sources
        training_missing=0
        training,training_missing=pilot.dataframe_rows(
            train_raw,rasters,xfm,cache)
        test,test_missing=pilot.dataframe_rows(
            test_raw,rasters,xfm,cache)
        np=sum(int(y) for y,x in training)
        nb=len(training)-np
        tp=sum(int(y) for y,x in test)
        tb=len(test)-tp
        if (tp!=original["test_source_matched_plant_recorded_cells"] or
            tb!=original["test_source_matched_background_cells"] or
            test_missing!=original["test_raster_nodata_excluded_cells"] or
            n_test_source_keys!=original["test_eligible_GBIF_dataset_keys"]):
            raise RuntimeError("HELDOUT_TEST_NOT_EXACTLY_ORIGINAL_SOURCE_"+species)
        row={
            "plant":species,
            "holdout_country":pilot.HOLDOUT,
            "training_focal_recorded_cells_source_disjoint":np,
            "training_background_cells_source_disjoint":nb,
            "training_raster_nodata_excluded_cells":training_missing,
            "training_dataset_country_contexts_source_disjoint":train_source_contexts,
            "test_focal_recorded_cells_unchanged":tp,
            "test_background_recorded_cells_unchanged":tb,
            "test_original_source_dataset_count_unchanged":n_test_source_keys,
            "test_raster_nodata_excluded_cells_unchanged":test_missing,
            "source_model_train_key_disjoint_from_original_CO":True,
            "train_source_intensity_recomputed_from_disjoint_datasets_only":True,
            "heldout_plant_source_records_or_cells_entered_model_training":False,
            "same_original_test_cells_for_paired_auc_comparison":True,
            "old_abiotic_AUC_same_test_cells":
                original["diagnostics"]["AUC_abiotic_only"],
            "old_source_intensity_AUC_same_test_cells":
                original["diagnostics"]["AUC_effort_only"],
            "old_abiotic_plus_intensity_AUC_same_test_cells":
                original["diagnostics"]["AUC_abiotic_plus_otherplant_effort"],
            "new_abiotic_AUC":None,
            "new_source_intensity_AUC":None,
            "new_abiotic_plus_intensity_AUC":None,
            "paired_delta_abiotic_AUC":None,
            "paired_delta_source_intensity_AUC":None,
            "paired_delta_abiotic_plus_intensity_AUC":None,
            "new_environment_gain_beyond_intensity_AUC":None,
            "new_exact_intensity_conditional_AUC":None,
            "new_exact_intensity_comparable_fraction":None
        }
        if min(np,nb)<20 or min(tp,tb)<5:
            row["status"]="SOURCE_DISJOINT_FIXED_SENTINEL_QUANTITY_STOP"
        else:
            fitted=diag.model_diagnostics(training,test)
            row.update({
                "new_abiotic_AUC":fitted["AUC_abiotic_only"],
                "new_source_intensity_AUC":fitted["AUC_effort_only"],
                "new_abiotic_plus_intensity_AUC":
                    fitted["AUC_abiotic_plus_otherplant_effort"],
                "paired_delta_abiotic_AUC":
                    fitted["AUC_abiotic_only"]-row["old_abiotic_AUC_same_test_cells"],
                "paired_delta_source_intensity_AUC":
                    fitted["AUC_effort_only"]-row["old_source_intensity_AUC_same_test_cells"],
                "paired_delta_abiotic_plus_intensity_AUC":
                    fitted["AUC_abiotic_plus_otherplant_effort"]-
                    row["old_abiotic_plus_intensity_AUC_same_test_cells"],
                "new_environment_gain_beyond_intensity_AUC":
                    fitted["increment_AUC_environment_beyond_effort_only"],
                "new_exact_intensity_conditional_AUC":
                    fitted["conditional_same_exact_effort_abiotic_plus_effort"]["auc"],
                "new_exact_intensity_comparable_fraction":
                    fitted["conditional_same_exact_effort_abiotic_plus_effort"]["comparable_pair_fraction"],
                "status":"SOURCE_DISJOINT_CO_FIXED_SENTINEL_PLANT_AUC"
            })
        results.append(row)
    return results


def execute():
    pilot.verified_v2_names()
    source_old=read(D/"plant_106x17_global_source_embargo_compact.json")
    if source_old.get("status")!=embargo.PASS_STATUS or \
       source_old["summary"]["source_disjoint_trainable_plant_species_all_17_holdouts"]!=35:
        raise RuntimeError("FULL_SOURCE_DATASET_EMBARGO_GATE_NOT_VERIFIED")
    source_receipt=verified_source(read(D/"gbif_download_submission.json"),
                                   read(D/"gbif_download_doi_poll.json"))
    meta=read(D/"gbif_archive_header_preflight.json")
    qc=read(D/"gbif_full_source_qc.json")
    names=name_map(read(D/"gbif_search_preflight.json"),
                   read(D/"plant_search_preflight.json"))
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    with tempfile.TemporaryDirectory(prefix="neobat-CO-cross-dataset-source-") as tmp:
        temp=pathlib.Path(tmp)
        plantfile=temp/"plant_original.zip"
        plant_source=source_receipt["plant"]
        if (plant_source["doi"]!=EXPECTED["plant"]["doi"] or
            plant_source["metadata_record_count"]!=EXPECTED["plant"]["n_records"]):
            raise RuntimeError("ORIGINAL_PLANT_SOURCE_DOI_COUNT_CHANGED")
        orig=safe_archive(plant_source["url"],plantfile)
        if (orig["sha256"]!=EXPECTED["plant"]["archive_sha"] or
            orig["sha256"]!=meta["files"]["plant"]["sha256"]):
            raise RuntimeError("ORIGINAL_PLANT_SOURCE_ARCHIVE_SHA_CHANGED")
        strict=strict_cell_records(plantfile,group="plant",
            source=meta["files"]["plant"],accepted=names["plant"],
            expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",strict,qc)
        source_keys,source_stats=embargo.source_embargo_from_archive(
            plantfile,meta["files"]["plant"],EXPECTED["plant"]["n_records"])
        banned=source_keys[pilot.HOLDOUT]
        prior_count=source_old["source_row_audit"]["source_dataset_country_counts"][pilot.HOLDOUT]
        if len(banned)!=prior_count:
            raise RuntimeError("CO_ORIGINAL_DATASETKEY_EMBARGO_CHANGED")
        source_index=source.country_dataset_cells(strict)
        raster_bytes,source_meta=pilot.verify_raster_sources(temp)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,raster_bytes)
            previously=replay_original_source_matched(strict,rasters,countries)
            fitted=evaluate(strict,source_index,banned,rasters,countries,previously)
    if len(fitted)!=3 or {x["plant"] for x in fitted}!=set(pilot.SENTINELS):
        raise RuntimeError("FROZEN_3_SENTINELS_MISSING")
    return {
        "schema_version":1,
        "status":PASS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "original_GBIF_plant_DOI":EXPECTED["plant"]["doi"],
        "original_GBIF_plant_ZIP_SHA256":orig["sha256"],
        "original_WorldClim_climate_ZIP_SHA256":source_meta["climate_zip_sha256"],
        "original_WorldClim_elevation_ZIP_SHA256":source_meta["elevation_zip_sha256"],
        "total_CO_original_dataset_keys_embargoed":len(banned),
        "original_three_previous_CO_plant_AUC_and_counts_exactly_replayed":True,
        "same_original_heldout_source_records_all_three":True,
        "original_country_universe_29":len(countries)==29,
        "source_disjoint_fit_successes":sum(x["status"]==
             "SOURCE_DISJOINT_CO_FIXED_SENTINEL_PLANT_AUC" for x in fitted),
        "source_quantity_or_nodata_stops":sum(x["status"]==
             "SOURCE_DISJOINT_FIXED_SENTINEL_QUANTITY_STOP" for x in fitted),
        "all_three_sentinels_kept":True,
        "plant_ecological_abundance_estimated":False,
        "independent_unopened_validation":False,
        "heldout_source_dataset_not_independent_institutions":True,
        "M3_minus_M1_bat_auc":None,
        "M3_minus_N1_bat_auc":None,
        "raw_original_plant_coords_or_dataset_keys_or_raster_pixels_persisted":False,
        "plants":fitted
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="build/neobat/CO_three_plant_disjoint_source_AUC.json")
    a=parser.parse_args()
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    try:result=execute()
    except Exception as exc:
        result={
            "schema_version":1,"status":STOP,
            "error_type":type(exc).__name__,
            "error_code":str(exc)[:220],
            "M3_minus_M1_bat_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_CO_SOURCE_DISJOINT_PLANT",result["status"],flush=True)
    for r in result.get("plants",[]):
        print("PLANT",r["plant"],"status",r["status"],
            "training_pos",r["training_focal_recorded_cells_source_disjoint"],
            "train_bg",r["training_background_cells_source_disjoint"],
            "test_pos",r["test_focal_recorded_cells_unchanged"],
            "new_aug_AUC",r["new_abiotic_plus_intensity_AUC"],
            "paired_AUC_change",r["paired_delta_abiotic_plus_intensity_AUC"],flush=True)
    return 0 if result["status"]==PASS else 3


if __name__=="__main__":
    raise SystemExit(main())
