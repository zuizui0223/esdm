"""NeoBat all 106 x 17 original source-matched plant transfer bias diagnostic.

Exploratory model *reporting-process* audit on already opened discovery GBIF,
NOT plant ecological-resource validation or bat M1/M3/N1. Full prespecified
1802 denominator. Source coordinates, 25km cell IDs, dataset keys, raster
pixels and per-cell model predictions are never exported.
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
from scripts import neobat_plant_within_dataset_source_gate as ds
from scripts import neobat_plant_effort_confounding_diagnostic as diag
from scripts.neobat_gbif_archive_header_preflight import verified_source, safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_106x17_SOURCE_INTENSITY_FULL_DIAGNOSTIC_FROZEN_20261119.md"
PREVIOUS=D/"plant_dataset_matched_106x17.json"
CO_PILOT=D/"plant_CO_source_datasetmatched_pilot.json"
STATUS_FITTED="EXPLORATORY_SOURCE_MATCHED_RANK_AUC"
STATUS_STOP="FIXED_FOLD_SOURCE_OR_RASTER_QUANTITY_STOP"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def qualified_observations(plant,country,original_country_taxa,source_matches):
    """Within source-matched cells, require an observed other plant in each role."""
    positive,background,n_datasets=source_matches[plant,country]
    original=original_country_taxa.get(country,{})
    retained=[]
    for cell in positive:
        values=original.get(cell,set())
        n_other=len(values)-int(plant in values)
        if n_other>0:
            retained.append((cell,1,math.log1p(n_other)))
    for cell in background:
        values=original.get(cell,set())
        if plant in values:raise RuntimeError("FOCAL_OBSERVATION_LEAKS_INTO_BACKGROUND")
        n_other=len(values)
        if n_other>0:
            retained.append((cell,0,math.log1p(n_other)))
    if len({r[0] for r in retained})!=len(retained):
        raise RuntimeError("SOURCE_MATCHED_CELL_PRESENT_IN_BOTH_CLASSES")
    return retained,n_datasets


def raster_screen(labeled,rasters,xfm,cache):
    rows=[]
    missing=0
    for cell,lab,effort in labeled:
        env=pilot.extract_environment(cell,rasters,xfm,cache)
        if env is None:
            missing+=1
        else:
            rows.append((cell,lab,(*env,effort)))
    return rows,missing


def known_truth_score(train,test):
    """Identical fixed sklearn settings as the original CO source-matched pilot."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score

    ytr=np.asarray([y for y,x in train],dtype=int)
    yte=np.asarray([y for y,x in test],dtype=int)
    xtr=np.asarray([x for y,x in train],dtype=float)
    xte=np.asarray([x for y,x in test],dtype=float)
    if xtr.ndim!=2 or xte.ndim!=2 or xtr.shape[1]!=4 or xte.shape[1]!=4:
        raise RuntimeError("SOURCE_MODEL_FEATURE_SCHEMA_STOP")
    if not np.all(np.isfinite(xtr)) or not np.all(np.isfinite(xte)):
        raise RuntimeError("NONFINITE_TRAIN_OR_TEST_FEATURES")
    if len(set(ytr))!=2 or len(set(yte))!=2:
        raise RuntimeError("SOURCE_RANK_BOTH_CLASSES_REQUIRED")
    summary={}
    combined_scores=None
    for name,cols in (
        ("abiotic_only",(0,1,2)),
        ("effort_only",(3,)),
        ("abiotic_plus_otherplant_effort",(0,1,2,3))
    ):
        scaler=StandardScaler().fit(xtr[:,cols])
        model=LogisticRegression(C=1.0,class_weight="balanced",
                                 max_iter=400,solver="lbfgs",random_state=20261119)
        model.fit(scaler.transform(xtr[:,cols]),ytr)
        scores=model.decision_function(scaler.transform(xte[:,cols]))
        summary["AUC_"+name]=float(roc_auc_score(yte,scores))
        if name=="abiotic_plus_otherplant_effort":
            combined_scores=list(map(float,scores))
    summary["delta_added_abiotic_beyond_source_intensity"]=(
        summary["AUC_abiotic_plus_otherplant_effort"]-summary["AUC_effort_only"])
    n_other=[int(round(math.expm1(float(x[3])))) for x in xte]
    summary["exact_intensity_conditional_auc"]=diag.conditional_auc(
        list(yte),combined_scores,n_other,binned=False)
    return summary


def summarise(rows):
    fitted=[x for x in rows if x["status"]==STATUS_FITTED]
    by_country=defaultdict(list)
    by_species=defaultdict(list)
    for row in fitted:
        by_country[row["holdout_country"]].append(row)
        by_species[row["plant"]].append(row)
    countries=sorted({x["holdout_country"] for x in rows})
    species=sorted({x["plant"] for x in rows})
    country_rows=[]
    for country in countries:
        rs=by_country[country]
        country_rows.append({
            "country":country,
            "original_plants":len(species),
            "fitted":len(rs),
            "source_or_raster_stops":len(species)-len(rs),
            "mean_delta_abiotic_beyond_intensity":None if not rs else
                sum(r["delta_added_abiotic_beyond_source_intensity"] for r in rs)/len(rs),
            "mean_auc_source_intensity_only":None if not rs else
                sum(r["AUC_effort_only"] for r in rs)/len(rs),
            "mean_auc_abiotic_only":None if not rs else
                sum(r["AUC_abiotic_only"] for r in rs)/len(rs)
        })
    species_rows=[]
    for plant in species:
        rs=by_species[plant]
        species_rows.append({
            "plant":plant,
            "original_countries":len(countries),
            "fitted":len(rs),
            "mean_delta_abiotic_beyond_intensity":None if not rs else
                sum(r["delta_added_abiotic_beyond_source_intensity"] for r in rs)/len(rs)
        })
    deltas=[r["delta_added_abiotic_beyond_source_intensity"] for r in fitted]
    countries_ok=[x for x in country_rows if x["fitted"]>0]
    if not countries_ok:raise RuntimeError("NO_FITTED_COUNTRY_FOR_DIAGNOSTIC")
    countrymeans=[x["mean_delta_abiotic_beyond_intensity"] for x in countries_ok]
    average=sum(countrymeans)/len(countrymeans)
    leave_one_out=[
        {"country_removed":x["country"],
         "equal_other_country_mean_delta":None if len(countrymeans)<2 else
          (sum(countrymeans)-x["mean_delta_abiotic_beyond_intensity"])/(len(countrymeans)-1)}
        for x in countries_ok
    ]
    n=len(fitted)
    return {
        "all_predeclared_species_country_pairs":len(rows),
        "source_and_model_fit_eligible":n,
        "source_or_raster_stopped":len(rows)-n,
        "all_species":len(species),
        "all_holdout_countries":len(countries),
        "countries_with_any_successful_fit":len(countries_ok),
        "fraction_with_positive_added_abiotic_delta":sum(x>0 for x in deltas)/n,
        "fraction_intensity_only_auc_gt_abiotic_only":sum(
            r["AUC_effort_only"]>r["AUC_abiotic_only"] for r in fitted)/n,
        "pair_weighted_mean_added_abiotic_delta":sum(deltas)/n,
        "equal_country_mean_added_abiotic_delta":average,
        "countries_with_mean_delta_gt_0":sum(x>0 for x in countrymeans),
        "countries_with_mean_delta_lt_0":sum(x<0 for x in countrymeans),
        "exact_intensity_conditional_auc_coverage_median":sorted(
            r["exact_intensity_conditional_auc"]["comparable_pair_fraction"]
            for r in fitted)[n//2],
        "conditional_auc_is_not_full_test_distribution":True,
        "equal_country_averages_not_independent_new_regions":True,
        "per_country":country_rows,
        "per_species":species_rows,
        "leave_one_country_out_mean_deltas":leave_one_out
    }


def evaluate(plant_cells,rasters,countries,holdouts,names,source_ref):
    from pyproj import Transformer

    per_dataset=ds.country_dataset_cells(plant_cells)
    country_taxa=pilot.country_cell_taxa(plant_cells)
    all_cells={country:set(mapping) for country,mapping in country_taxa.items()}
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    rastercache={}
    prior={(r["plant"],r["holdout_country"]):r
           for r in source_ref["plant_country_source_support"]}
    if len(prior)!=1802:
        raise RuntimeError("PREVIOUS_FROZEN_1802_SOURCE_GATE_INCOMPLETE")
    co_ref=read(CO_PILOT)
    if co_ref.get("status")!="EXPLORATORY_ORIGINAL_DATASETMATCHED_3PLANT_CO_MODEL_COMPLETE":
        raise RuntimeError("PREVIOUS_THREE_SENTINEL_RESULT_NOT_VERIFIED")
    co_lookup={r["plant"]:r for r in co_ref["plants"]}
    rows=[]
    previous_matched_train=previous_matched_eval=0
    co_replay=0
    for i,plant in enumerate(names):
        matches={(plant,cc):ds.source_matched_country(plant,cc,plant_cells,per_dataset)
                 for cc in countries}
        # Preserve each context's within-original-dataset/recording-intensity
        # selection as a precomputed per-species in-RAM cell list.
        model_cells={}
        for country in countries:
            raw,nds=qualified_observations(plant,country,country_taxa,matches)
            model_cells[country],lost=raster_screen(raw,rasters,xfm,rastercache)
            # Count no-data loss only; all raw source cells never leave RAM.
            model_cells[country+"_nodata"]=lost

        for holdout in holdouts:
            frozen=prior[plant,holdout]
            gate=ds.fold_counts(plant,holdout,matches,all_cells,countries)
            for k in (
                "train_focal_source_matched_recorded_cells",
                "train_source_matched_otherplant_bg_cells",
                "test_focal_source_matched_recorded_cells",
                "test_source_matched_otherplant_bg_cells",
                "test_eligible_GBIF_dataset_keys"
            ):
                if gate[k]!=frozen[k]:
                    raise RuntimeError("PREVIOUS_SOURCE_1802_DENOMINATOR_DRIFT:"+k)
            previous_matched_train+=int(gate["source_matched_training_quantity_qualified"])
            previous_matched_eval+=int(gate["source_matched_heldout_scoring_quantity_qualified"])

            banned=all_cells.get(holdout,set())
            tr=[(lab,feat) for country in countries if country!=holdout
                for cell,lab,feat in model_cells[country] if cell not in banned]
            te=[(lab,feat) for cell,lab,feat in model_cells[holdout]]
            trainp=sum(int(y) for y,_ in tr)
            testp=sum(int(y) for y,_ in te)
            trainbg=len(tr)-trainp
            testbg=len(te)-testp
            row={
                "plant":plant,"holdout_country":holdout,
                "status":STATUS_STOP,
                "source_matched_trainability_previous_gate":bool(gate["source_matched_training_quantity_qualified"]),
                "source_matched_heldout_test_quantity_previous_gate":bool(gate["source_matched_heldout_scoring_quantity_qualified"]),
                "train_positive_recorded_cells":trainp,
                "train_pseudo_background_cells":trainbg,
                "heldout_positive_recorded_cells":testp,
                "heldout_pseudo_background_cells":testbg,
                "heldout_raster_nodata_removed_cells":model_cells[holdout+"_nodata"],
                "test_country_plant_records_used_to_train":False,
                "crossborder_25km_cell_overlap_removed":True,
                "pseudo_background_is_not_absence":True,
                "source_intensity_independently_measured_effort":False,
                "AUC_abiotic_only":None,
                "AUC_effort_only":None,
                "AUC_abiotic_plus_otherplant_effort":None,
                "delta_added_abiotic_beyond_source_intensity":None,
                "exact_intensity_conditional_auc":None
            }
            if min(trainp,trainbg)>=20 and min(testp,testbg)>=5:
                result=known_truth_score(tr,te)
                row.update(result)
                row["status"]=STATUS_FITTED
            if row["status"]==STATUS_FITTED and not gate["source_matched_heldout_scoring_quantity_qualified"]:
                raise RuntimeError("FITTED_FOLD_OUTSIDE_FROZEN_677_SOURCE_GATE")
            if holdout=="CO" and plant in co_lookup:
                # The prior 3-sentinel case is a frozen external
                # implementation regression, not a new heldout dataset.
                old=co_lookup[plant]
                for new_key,old_key in (
                    ("train_positive_recorded_cells","train_source_matched_plant_recorded_cells"),
                    ("train_pseudo_background_cells","train_source_matched_background_cells"),
                    ("heldout_positive_recorded_cells","test_source_matched_plant_recorded_cells"),
                    ("heldout_pseudo_background_cells","test_source_matched_background_cells")
                ):
                    if row[new_key]!=old[old_key]:
                        raise RuntimeError("FROZEN_CO_SOURCE_MATCHED_SENTINEL_DENOMINATOR_DRIFT")
                if row["status"]!=STATUS_FITTED:
                    raise RuntimeError("FROZEN_CO_SENTINEL_FIT_NOW_FAILED")
                for key in ("AUC_abiotic_only","AUC_effort_only","AUC_abiotic_plus_otherplant_effort"):
                    if not math.isclose(row[key],old["diagnostics"][key],rel_tol=0,abs_tol=1e-10):
                        raise RuntimeError("FROZEN_CO_SENTINEL_AUC_REPLAY_FAILED:"+key)
                co_replay+=1
            rows.append(row)
    if len(rows)!=1802 or co_replay!=3:
        raise RuntimeError("FROZEN_1802_OR_THREE_SENTINEL_REPLAY_STOP")
    if previous_matched_train!=1802 or previous_matched_eval!=677:
        raise RuntimeError("ORIGINAL_DATASET_SOURCE_GATE_QUANTITY_DRIFT")
    return rows,summarise(rows),len(rastercache)


def execute():
    names,holdouts=ds.fixed_names_and_countries()
    original_gate=read(PREVIOUS)
    if (original_gate.get("status")!="DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY"
        or original_gate["summary"]["source_matched_train_and_test_scoring_pairs"]!=677):
        raise RuntimeError("PREVIOUS_106x17_COUNTRY_MATCHED_GATE_MISSING")
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    meta=read(D/"gbif_archive_header_preflight.json")
    source=verified_source(read(D/"gbif_download_submission.json"),
                           read(D/"gbif_download_doi_poll.json"))
    qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    if source["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
       source["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
        raise RuntimeError("ORIGINAL_DOI_OR_SOURCE_ROW_COUNT_CHANGED")
    with tempfile.TemporaryDirectory(prefix="neobat-source-intensity-all106-") as t:
        directory=pathlib.Path(t)
        original_zip=directory/"original_plants.zip"
        observed=safe_archive(source["plant"]["url"],original_zip)
        if observed["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           observed["sha256"]!=meta["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_PLANT_ZIP_SHA_CHANGED")
        cells=strict_cell_records(original_zip,group="plant",
            source=meta["files"]["plant"],accepted=accepted["plant"],
            expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,qc)
        members,raster_source=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,members)
            rows,aggregate,source_cells_sampled=evaluate(
                cells,rasters,countries,holdouts,names,original_gate)
    return {
        "schema_version":1,
        "status":"EXPLORATORY_106x17_SOURCE_MATCHED_INTENSITY_DIAGNOSTIC_COMPLETE",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "design":DESIGN,
        "GBIF_plant_original_DOI":EXPECTED["plant"]["doi"],
        "GBIF_plant_original_zip_sha256":observed["sha256"],
        "frozen_106_plant_universe_sha256":ds.FROZEN_V2_SHA,
        "source_18_hundred_pairs_replayed":True,
        "raster_source":raster_source,
        "unique_raster_cell_source_centers_sampled_in_memory_only":source_cells_sampled,
        "original_3_sentinel_CO_model_AUC_and_cells_exactly_replayed":True,
        "not_independent_holdout_and_not_deployable_suitability":True,
        "source_derived_intensity_computed_from_test_country_records":True,
        "original_locations_datasetIDs_and_percell_predictions_written":False,
        "bat_M3_minus_M1_auc":None,
        "bat_M3_minus_N1_auc":None,
        "summary":aggregate,
        "all_1802_fold_rows":rows
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_106x17_source_intensity_diagnostic.json")
    p.add_argument("--compact",default="build/neobat/plant_106x17_source_intensity_compact.json")
    args=p.parse_args()
    out=pathlib.Path(args.out);compact=pathlib.Path(args.compact)
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={"schema_version":1,
                "status":"SOURCE_MATCHED_INTENSITY_106x17_DIAGNOSTIC_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:250],
                "bat_M3_minus_M1_auc":None}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    trimmed={k:v for k,v in result.items() if k!="all_1802_fold_rows"}
    compact.write_text(json.dumps(trimmed,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_106x17_INTENSITY",result["status"],flush=True)
    if "summary" in result:
        a=result["summary"]
        print("INTENSITY_FOLDS",a["source_and_model_fit_eligible"],
              "COUNTRIES",a["countries_with_any_successful_fit"],flush=True)
        print("INTENSITY_DELTA_COUNTRY_EQUAL",a["equal_country_mean_added_abiotic_delta"],flush=True)
    return 0 if result["status"]=="EXPLORATORY_106x17_SOURCE_MATCHED_INTENSITY_DIAGNOSTIC_COMPLETE" else 3


if __name__=="__main__":
    raise SystemExit(main())
