"""Fixed 106×17 NeoBat plant original GBIF source-intensity portability audit.

Exploratory source/observation model ONLY: no bat M1/M3/N1 effect, no
plant true occupancy/food abundance and no unopened independent validation.
All original source model ranks and stopped folds are aggregate-only.
"""
from __future__ import annotations
import argparse,hashlib,json,math,pathlib,tempfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts import neobat_plant_effort_confounding_diagnostic as diag
from scripts import neobat_plant_source_matched_co_pilot as matched
from scripts import neobat_plant_within_dataset_source_gate as ds
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_106x17_PLANT_SOURCE_EFFORT_TRANSFER_FROZEN_20261119.md"
N_FIXED=106*17
SEED=20261119
CLIMATE_COLS=(0,1,2)
EFFORT_COLS=(3,)
COMBINED_COLS=(0,1,2,3)


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def measure_three(train,test):
    """Identical numerical engine to frozen three-sentinel source model."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    Xtr=np.asarray([x for y,x in train],dtype=float)
    ytr=np.asarray([int(y) for y,x in train],dtype=int)
    Xte=np.asarray([x for y,x in test],dtype=float)
    yte=np.asarray([int(y) for y,x in test],dtype=int)
    if Xtr.shape[1]!=4 or Xte.shape[1]!=4 or len(set(ytr))!=2 or len(set(yte))!=2:
        raise ValueError("CROSSFIT_CLASS_FEATURE_STOP")
    if not np.all(np.isfinite(Xtr)) or not np.all(np.isfinite(Xte)):
        raise ValueError("CROSSFIT_NONFINITE_FEATURE")
    result={}
    for name,cols in (
        ("abiotic_only",CLIMATE_COLS),
        ("source_record_intensity_only",EFFORT_COLS),
        ("abiotic_plus_source_record_intensity",COMBINED_COLS)
    ):
        scaler=StandardScaler().fit(Xtr[:,cols])
        mod=LogisticRegression(C=1.0,class_weight="balanced",
             max_iter=400,solver="lbfgs",random_state=SEED)
        mod.fit(scaler.transform(Xtr[:,cols]),ytr)
        rank=mod.decision_function(scaler.transform(Xte[:,cols]))
        result[name]={
            "heldout_source_rank_auc":float(roc_auc_score(yte,rank)),
            "scores":rank if name=="abiotic_plus_source_record_intensity" else None
        }
    combined=result["abiotic_plus_source_record_intensity"]["scores"]
    n_other=[int(round(math.expm1(float(x[3])))) for x in Xte]
    conditional=diag.conditional_auc(list(yte),list(combined),n_other,binned=False)
    return {
       "AUC_abiotic_only":result["abiotic_only"]["heldout_source_rank_auc"],
       "AUC_source_intensity_only":result["source_record_intensity_only"]["heldout_source_rank_auc"],
       "AUC_abiotic_plus_source_intensity":
           result["abiotic_plus_source_record_intensity"]["heldout_source_rank_auc"],
       "delta_AUC_abiotic_added_to_source_intensity":
           (result["abiotic_plus_source_record_intensity"]["heldout_source_rank_auc"]-
            result["source_record_intensity_only"]["heldout_source_rank_auc"]),
       "exact_same_intensity_heldout_AUC":conditional["auc"],
       "exact_same_intensity_comparable_pair_fraction":conditional["comparable_pair_fraction"],
       "exact_same_intensity_comparable_pairs":conditional["comparable_positive_background_pairs"]
    }


def candidate_folds(plant_cells,names,holdouts,universe,rasters):
    from pyproj import Transformer
    if len(names)!=106 or len(holdouts)!=17 or len(universe)!=29:
        raise RuntimeError("FULL_106x17_COUNTRY_DENOMINATOR_STOP")
    global_country_taxa=pilot.country_cell_taxa(plant_cells)
    source_matched=ds.all_country_source_matches(names,plant_cells,universe)
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    features={}
    excluded_by_holdout={country:set(global_country_taxa.get(country,{}))
                         for country in holdouts}
    old=read(D/"plant_CO_source_datasetmatched_pilot.json")
    sentinel_prior={x["plant"]:x for x in old["plants"]}
    if old["status"]!="EXPLORATORY_ORIGINAL_DATASETMATCHED_3PLANT_CO_MODEL_COMPLETE" or \
       set(sentinel_prior)!=set(pilot.SENTINELS):
        raise RuntimeError("ORIGINAL_MATCHED_CO_SENTINEL_RECEIPT_INVALID")
    replay_count=0
    rows=[]
    for number,taxon in enumerate(names,1):
        # Compute source-only cells once per taxon×country, no model
        # scores or heldout labels used to select source populations.
        seen={}
        for country in universe:
            seen[country],_ = matched.source_filtered_observation_cells(
                global_country_taxa,source_matched,taxon,country)
        for holdout in holdouts:
            training=[]
            excluded=excluded_by_holdout[holdout]
            for country in universe:
                if country==holdout:continue
                training.extend(x for x in seen[country] if x[0] not in excluded)
            test=seen[holdout]
            train_rows,train_nodata=pilot.dataframe_rows(training,rasters,xfm,features)
            test_rows,test_nodata=pilot.dataframe_rows(test,rasters,xfm,features)
            train_p=sum(int(y) for y,x in train_rows)
            test_p=sum(int(y) for y,x in test_rows)
            train_bg=len(train_rows)-train_p
            test_bg=len(test_rows)-test_p
            row={
                "plant":taxon,"holdout_country":holdout,
                "train_source_matched_focal_cells":train_p,
                "train_source_matched_target_background_cells":train_bg,
                "heldout_source_matched_focal_cells":test_p,
                "heldout_source_matched_target_background_cells":test_bg,
                "training_abiotic_nodata_cell_exclusions":train_nodata,
                "heldout_abiotic_nodata_cell_exclusions":test_nodata,
                "heldout_occurrences_used_in_training":False,
                "target_background_is_not_true_absence":True,
                "same_GBIF_datasetKey_is_not_independent_event":True,
                "AUC_abiotic_only":None,
                "AUC_source_intensity_only":None,
                "AUC_abiotic_plus_source_intensity":None,
                "delta_AUC_abiotic_added_to_source_intensity":None,
                "exact_same_intensity_heldout_AUC":None,
                "exact_same_intensity_comparable_pair_fraction":None
            }
            if min(train_p,train_bg)<20:
                row["status"]="PLANT_SOURCE_MATCHED_TRAIN_QUANTITY_STOP"
            elif min(test_p,test_bg)<5:
                row["status"]="PLANT_SOURCE_MATCHED_HELDOUT_QUANTITY_STOP"
            else:
                scores=measure_three(train_rows,test_rows)
                row.update(scores)
                row["status"]="EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC"
            if holdout=="CO" and taxon in sentinel_prior:
                ref=sentinel_prior[taxon]
                # Replay exact old three-sentinel retained raw-source and
                # targetgroup criteria before allowing any large summary.
                if (train_p!=ref["train_source_matched_plant_recorded_cells"] or
                    train_bg!=ref["train_source_matched_background_cells"] or
                    test_p!=ref["test_source_matched_plant_recorded_cells"] or
                    test_bg!=ref["test_source_matched_background_cells"] or
                    row["status"]!="EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC"):
                    raise RuntimeError("ORIGINAL_3SENTINEL_CO_SOURCE_COUNTS_DRIFT_"+taxon)
                diag0=ref["diagnostics"]
                for key,source_key in [
                    ("AUC_abiotic_only","AUC_abiotic_only"),
                    ("AUC_source_intensity_only","AUC_effort_only"),
                    ("AUC_abiotic_plus_source_intensity","AUC_abiotic_plus_otherplant_effort")
                ]:
                    if not math.isclose(row[key],diag0[source_key],abs_tol=1e-12):
                        raise RuntimeError("ORIGINAL_3SENTINEL_CO_AUC_DRIFT_"+taxon+"_"+key)
                replay_count+=1
            rows.append(row)
        if number%20==0:
            print("NEOBAT_SOURCE_RANK_PROGRESS_SPECIES",number,flush=True)
    if len(rows)!=N_FIXED or replay_count!=3:
        raise RuntimeError("ALL_1802_ROWS_OR_3_CO_SENTINEL_REPLAY_MISSING")
    return rows,replay_count


def summarize(rows):
    from statistics import mean
    import random
    values=[x for x in rows if x["status"]=="EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC"]
    deltas=[float(x["delta_AUC_abiotic_added_to_source_intensity"]) for x in values]
    by_country=defaultdict(list)
    by_plant=defaultdict(list)
    for row in values:
        by_country[row["holdout_country"]].append(
            row["delta_AUC_abiotic_added_to_source_intensity"])
        by_plant[row["plant"]].append(
            row["delta_AUC_abiotic_added_to_source_intensity"])
    country_means={c:mean(xs) for c,xs in by_country.items()}
    plant_means={p:mean(xs) for p,xs in by_plant.items()}
    per_country=[{
       "country":country,
       "original_fixed_plants":106,
       "heldout_scored_plants":len(by_country.get(country,[])),
       "country_equal_plant_delta_AUC_mean":country_means.get(country),
    } for country in sorted({x["holdout_country"] for x in rows})]
    countries=list(country_means)
    if not countries:
        raise RuntimeError("NO_PLANT_COUNTRY_HELDOUT_RANK_SCORES")
    rng=random.Random(SEED)
    bootstrap=[mean([country_means[rng.choice(countries)]
                     for i in countries]) for _ in range(2000)]
    bootstrap.sort()
    loco=[mean([country_means[c] for c in countries if c!=d])
          for d in countries] if len(countries)>1 else []
    return {
        "fixed_full_cohort_pair_denominator":N_FIXED,
        "source_matched_plant_country_rank_AUC_measured":len(values),
        "source_or_nodata_quantity_STOP_pairs":N_FIXED-len(values),
        "eligible_original_plant_species":len(plant_means),
        "eligible_original_holdout_countries":len(country_means),
        "per_plantcountry_equal_delta_AUC_mean":mean(deltas),
        "per_country_equal_delta_AUC_mean":mean(country_means.values()),
        "per_species_equal_delta_AUC_mean":mean(plant_means.values()),
        "country_cluster_bootstrap_2000_percentile_interval":[
            bootstrap[int(0.025*(len(bootstrap)-1))],
            bootstrap[int(0.975*(len(bootstrap)-1))],
        ],
        "leave_one_country_out_country_equal_mean_range":[min(loco),max(loco)] if loco else None,
        "proportion_eligible_folds_abiotic_addition_positive":sum(x>0 for x in deltas)/len(deltas),
        "proportion_eligible_folds_abiotic_addition_gt_0p02":sum(x>0.02 for x in deltas)/len(deltas),
        "proportion_eligible_folds_abiotic_addition_lt_minus0p02":sum(x<-.02 for x in deltas)/len(deltas),
        "country_cluster_interval_is_exploratory_same_source_not_independent_studies":True,
        "per_country":per_country
    }


def execute():
    names,holdouts=ds.fixed_names_and_countries()
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
       "GBIF_29_country_universe"]
    if len(countries)!=29 or len(holdouts)!=17:raise RuntimeError("SOURCE_COUNTRY_COUNT_STOP")
    src=verified_source(read(D/"gbif_download_submission.json"),
                        read(D/"gbif_download_doi_poll.json"))
    header=read(D/"gbif_archive_header_preflight.json")
    qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    with tempfile.TemporaryDirectory(prefix="neobat-106x17-source-rank-") as tmp:
        directory=pathlib.Path(tmp)
        archive=directory/"source_original_plant.zip"
        resultzip=safe_archive(src["plant"]["url"],archive)
        if resultzip["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           resultzip["sha256"]!=header["files"]["plant"]["sha256"]:
            raise RuntimeError("SOURCE_PLANT_ZIP_SHA_STOP")
        cells=strict_cell_records(archive,group="plant",
              source=header["files"]["plant"],accepted=accepted["plant"],
              expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,qc)
        raster_members,meta=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,raster_members)
            rows,replay=candidate_folds(cells,names,holdouts,countries,rasters)
    summary=summarize(rows)
    summary["original_3sentinel_Colombia_source_matched_model_replays"]=replay
    return {
       "schema_version":1,
       "status":"EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE",
       "created_utc":datetime.now(timezone.utc).isoformat(),
       "frozen_design":DESIGN,
       "original_plant_GBIF_DOI":EXPECTED["plant"]["doi"],
       "original_plant_ZIP_SHA256":resultzip["sha256"],
       "WorldClim_climate_ZIP_SHA256":meta["climate_zip_sha256"],
       "WorldClim_elevation_ZIP_SHA256":meta["elevation_zip_sha256"],
       "frozen_106_species_universe_sha256":pilot.V2_HASH,
       "original_1802_species_country_pairs_unmodified":True,
       "previous_3sentinel_CO_AUCs_exactly_replayed":True,
       "discovery_source_previously_opened_not_confirmatory":True,
       "same_dataset_source_matching_not_detection_effort":True,
       "rank_AUC_is_target_group_source_recording_not_plant_occupancy":True,
       "no_bat_M1_M3_N1_ecological_fit":True,
       "M3_minus_M1_bat_auc":None,
       "M3_minus_N1_bat_auc":None,
       "no_raw_coords_pixels_per_cell_scores_or_GBIF_datasetIDs_saved":True,
       "summary":summary,
       "plant_country_source_rank_results":rows
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_106x17_source_effort_transfer.json")
    p.add_argument("--compact",default="build/neobat/plant_106x17_source_effort_transfer_compact.json")
    args=p.parse_args()
    out=pathlib.Path(args.out);compact=pathlib.Path(args.compact)
    out.parent.mkdir(parents=True,exist_ok=True);compact.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={
            "schema_version":1,"status":"PLANT_106x17_SOURCE_TRANSFER_STOP",
            "error_type":type(exc).__name__,"error_code":str(exc)[:220],
            "M3_minus_M1_bat_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    compact.write_text(json.dumps({
        k:v for k,v in result.items() if k!="plant_country_source_rank_results"
    },indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_106x17_PLANT_TRANSFER",result["status"],flush=True)
    if "summary" in result:
        print("SOURCE_EFFORT_TRANSFER_SUMMARY",json.dumps({
            k:v for k,v in result["summary"].items() if k!="per_country"
        },sort_keys=True),flush=True)
    return 0 if result["status"]=="EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE" else 3


if __name__=="__main__":
    raise SystemExit(main())
