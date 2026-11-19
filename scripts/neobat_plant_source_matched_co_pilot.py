"""NeoBat original plant DOI Colombia-heldout source-dataset-matched AUC pilot.

Post-hoc exploratory reanalysis with SAME 3 frozen taxa and model settings.
The only new cohort criterion is same GBIF datasetKey source collections
for positives vs pseudo-background. Not matched sampling events/true absence.
"""
from __future__ import annotations
import argparse,json,pathlib,tempfile
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts import neobat_plant_effort_confounding_diagnostic as diag
from scripts import neobat_plant_within_dataset_source_gate as ds
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_SOURCE_DATASET_MATCHED_3PLANT_CO_PILOT_FROZEN_20261119.md"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def source_filtered_observation_cells(global_country_taxa,source_matches,taxon,country,excluded=frozenset()):
    """Use already-fixed same-source selection + >=1 other plant in both roles."""
    if (taxon,country) not in source_matches:
        raise ValueError("DATASET_MATCHED_SOURCE_MISSING_PLANT_COUNTRY")
    positive,background,n_datasets=source_matches[taxon,country]
    observations=pilot.make_labeled_cells(global_country_taxa,taxon,country,
                                           excluded_cells=excluded)
    retained=[
        x for x in observations
        if (x[1]==1 and x[0] in positive) or
           (x[1]==0 and x[0] in background)
    ]
    if len(retained)!=len(set(x[0] for x in retained)):
        raise RuntimeError("DUPLICATE_SOURCE_MATCHED_CELL")
    return retained,n_datasets


def fit_sentinels(plant_cells,rasters,countries):
    from pyproj import Transformer
    pilot.verified_v2_names()
    if pilot.HOLDOUT not in countries or len(countries)!=29:
        raise RuntimeError("ORIGINAL_SOURCE_COUNTRY_UNIVERSE_DRIFT")
    global_country_taxa=pilot.country_cell_taxa(plant_cells)
    matched=ds.all_country_source_matches(
        pilot.SENTINELS,plant_cells,countries)
    if len(matched)!=len(pilot.SENTINELS)*len(countries):
        raise RuntimeError("THREE_SENTINEL_COUNTRY_MATCH_MATRIX_DRIFT")
    heldout_cells=set(global_country_taxa[pilot.HOLDOUT])
    converter=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    cache={}
    old=read(D/"plant_colombia_crossfit_pilot.json")
    old_by={x["plant"]:x for x in old["plants"]}
    if old["status"]!="EXPLORATORY_COUNTRY_EXCLUDED_3PLANT_PILOT_COMPLETE" or \
       set(old_by)!=set(pilot.SENTINELS):
        raise RuntimeError("ORIGINAL_THREE_SENTINEL_RECEIPT_DRIFT")
    result=[]
    for focal in pilot.SENTINELS:
        train_labeled=[]
        train_eligible_ds_contexts=0
        for country in countries:
            if country==pilot.HOLDOUT:continue
            data,nds=source_filtered_observation_cells(
                global_country_taxa,matched,focal,country,heldout_cells)
            train_labeled.extend(data)
            train_eligible_ds_contexts+=nds
        heldout_labeled,n_test_ds=source_filtered_observation_cells(
            global_country_taxa,matched,focal,pilot.HOLDOUT)
        train,n_train_nodata=pilot.dataframe_rows(train_labeled,rasters,converter,cache)
        heldout,n_test_nodata=pilot.dataframe_rows(heldout_labeled,rasters,converter,cache)
        p_train=sum(y for y,x in train);p_test=sum(y for y,x in heldout)
        bg_train=len(train)-p_train;bg_test=len(heldout)-p_test
        row={
            "plant":focal,"heldout_country":pilot.HOLDOUT,
            "train_source_matched_plant_recorded_cells":p_train,
            "train_source_matched_background_cells":bg_train,
            "test_source_matched_plant_recorded_cells":p_test,
            "test_source_matched_background_cells":bg_test,
            "train_source_matched_dataset_country_contexts":train_eligible_ds_contexts,
            "test_eligible_GBIF_dataset_keys":n_test_ds,
            "train_raster_nodata_excluded_cells":n_train_nodata,
            "test_raster_nodata_excluded_cells":n_test_nodata,
            "same_source_dataset_is_not_same_sampling_event":True,
            "heldout_country_plant_rows_enter_training":False,
            "crossborder_shared_25km_source_cells_enter_training":False,
            "source_background_is_not_true_absence":True,
            "old_abiotic_AUC_different_background_unpaired":old_by[focal]["AUC_abiotic_only"],
            "old_abiotic_plus_effort_AUC_different_background_unpaired":
                old_by[focal]["AUC_abiotic_plus_otherplant_effort"],
            "diagnostics":None
        }
        if min(p_train,bg_train)<20 or min(p_test,bg_test)<5:
            row["status"]="SOURCE_MATCHED_PLANT_CROSSFIT_QUANTITY_STOP"
        else:
            row["diagnostics"]=diag.model_diagnostics(train,heldout)
            row["status"]="SOURCE_MATCHED_COUNTRY_HELDOUT_PLANT_PILOT_AUC"
        result.append(row)
    return result


def execute():
    pilot.verified_v2_names()
    sources=verified_source(read(D/"gbif_download_submission.json"),
                            read(D/"gbif_download_doi_poll.json"))
    head=read(D/"gbif_archive_header_preflight.json")
    qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    if sources["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
       sources["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
        raise RuntimeError("PLANT_ORIGINAL_DOI_OR_RECORDS_CHANGED")
    with tempfile.TemporaryDirectory(prefix="neobat-original-datasetmatched-plant-model-") as tmp:
        directory=pathlib.Path(tmp)
        plant_zip=directory/"original_plants.zip"
        original=safe_archive(sources["plant"]["url"],plant_zip)
        if original["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           original["sha256"]!=head["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_PLANT_ZIP_SHA_DRIFT")
        cells=strict_cell_records(plant_zip,group="plant",
            source=head["files"]["plant"],
            accepted=accepted["plant"],expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,qc)
        members,rasters_meta=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,members)
            fitted=fit_sentinels(cells,rasters,countries)
    return {
      "schema_version":1,
      "status":"EXPLORATORY_ORIGINAL_DATASETMATCHED_3PLANT_CO_MODEL_COMPLETE",
      "created_utc":datetime.now(timezone.utc).isoformat(),
      "frozen_design":DESIGN,
      "GBIF_plant_source_DOI":EXPECTED["plant"]["doi"],
      "GBIF_plant_original_archive_SHA256":original["sha256"],
      "WorldClim_climate_original_archive_SHA256":rasters_meta["climate_zip_sha256"],
      "WorldClim_elevation_original_archive_SHA256":rasters_meta["elevation_zip_sha256"],
      "frozen_106_species_universe_SHA256":pilot.V2_HASH,
      "heldout_country":pilot.HOLDOUT,
      "same_original_three_sentinel_species":list(pilot.SENTINELS),
      "source_matched_model_evaluated":sum(
          x["status"]=="SOURCE_MATCHED_COUNTRY_HELDOUT_PLANT_PILOT_AUC" for x in fitted),
      "source_matched_model_quantity_stopped":sum(
          x["status"]=="SOURCE_MATCHED_PLANT_CROSSFIT_QUANTITY_STOP" for x in fitted),
      "same_source_not_independent_survey_effort":True,
      "previous_and_current_AUC_not_paired_same_test_population":True,
      "not_106x17_complete_ecological_resource_SDM":True,
      "M3_minus_M1_bat_auc":None,
      "M3_minus_N1_bat_auc":None,
      "no_original_coords_cellIDs_datasetIDs_or_pixels_persisted":True,
      "plants":fitted
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_CO_source_datasetmatched_pilot.json")
    a=p.parse_args();out=pathlib.Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try: result=execute()
    except Exception as exc:
        result={
          "schema_version":1,
          "status":"DATASETMATCHED_PLANT_MODEL_SOURCE_OR_QUALIFICATION_STOP",
          "error_type":type(exc).__name__,"error_code":str(exc)[:210],
          "M3_minus_M1_bat_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_SOURCE_MATCHED_THREE_PLANTS",result["status"],flush=True)
    for r in result.get("plants",[]):
        print("SOURCE_MATCHED_PLANT",r["plant"],"test_pos",
              r["test_source_matched_plant_recorded_cells"],"test_bg",
              r["test_source_matched_background_cells"],"status",r["status"],
              "effort_AUC",r["diagnostics"]["AUC_effort_only"] if r["diagnostics"] else None,flush=True)
    return 0 if result["status"]=="EXPLORATORY_ORIGINAL_DATASETMATCHED_3PLANT_CO_MODEL_COMPLETE" else 3


if __name__=="__main__":
    raise SystemExit(main())
