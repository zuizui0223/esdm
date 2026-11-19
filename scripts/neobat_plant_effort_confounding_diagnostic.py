"""Post-hoc NeoBat plant source-effort confounding diagnostic.

Replays the immutable 3-sentinel Colombia-outcountry original plant fit,
adds effort-only baseline and exact/known-bin source-intensity-conditional AUC.
Original pilot program/result and v1 bat SDM contract remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import tempfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as pilot
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_PLANT_GBIF_EFFORT_DIAGNOSTIC_FROZEN_20261119.md"
OLD="docs/replication/neobat/plant_colombia_crossfit_pilot.json"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def bin_group(n):
    if n==1:return 0
    if 2<=n<=3:return 1
    if 4<=n<=7:return 2
    return 3


def conditional_auc(labels,scores,effort_n,*,binned):
    from scripts.neobat_model_comparison_core import rank_auc
    grouped=defaultdict(list)
    for lab,score,n in zip(labels,scores,effort_n):
        if lab not in (0,1) or not math.isfinite(score) or n<1:
            raise ValueError("CONDITIONAL_NONFINITE_OR_INVALID_TARGETGROUP")
        grouped[bin_group(n) if binned else n].append((lab,score))
    np=sum(labels); nb=len(labels)-np
    if np<1 or nb<1:raise ValueError("CONDITIONAL_BOTH_CLASSES_REQUIRED")
    totpairs=np*nb
    available=0; numerator=0.0
    for values in grouped.values():
        ys=[x[0] for x in values]
        ps=sum(ys); bs=len(values)-ps
        if ps==0 or bs==0:continue
        samepairs=ps*bs
        auc=rank_auc(ys,[x[1] for x in values])
        available+=samepairs
        numerator+=samepairs*auc
    return {
        "auc":None if available==0 else numerator/available,
        "comparable_positive_background_pairs":available,
        "all_possible_positive_background_pairs":totpairs,
        "comparable_pair_fraction":available/totpairs,
        "source_effort_strata_with_both_classes":sum(
            any(z[0]==0 for z in values) and any(z[0]==1 for z in values)
            for values in grouped.values())
    }


def model_diagnostics(train,test):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    Xtrain=np.asarray([x for y,x in train],dtype=float)
    ytrain=np.asarray([y for y,x in train],dtype=int)
    Xtest=np.asarray([x for y,x in test],dtype=float)
    ytest=np.asarray([y for y,x in test],dtype=int)
    if Xtrain.shape[1]!=4 or Xtest.shape[1]!=4 or len(set(ytrain))!=2 or len(set(ytest))!=2:
        raise ValueError("SOURCE_DIAGNOSTIC_SHAPE_OR_CLASS_STOP")
    if not np.all(np.isfinite(Xtrain)) or not np.all(np.isfinite(Xtest)):
        raise ValueError("NONFINITE_SOURCE_FEATURE")
    expected=pilot.train_and_score(train,test)
    scores={}
    ranks={}
    for name,cols in (
        ("abiotic_only",(0,1,2)),
        ("effort_only",(3,)),
        ("abiotic_plus_other_plant_effort",(0,1,2,3))
    ):
        sc=StandardScaler().fit(Xtrain[:,cols])
        mod=LogisticRegression(C=1.0,class_weight="balanced",
             max_iter=400,solver="lbfgs",random_state=20261119)
        mod.fit(sc.transform(Xtrain[:,cols]),ytrain)
        val=mod.decision_function(sc.transform(Xtest[:,cols]))
        scores[name]=float(roc_auc_score(ytest,val))
        ranks[name]=list(map(float,val))
    for name,value in expected.items():
        if not math.isclose(scores[name],value,rel_tol=0,abs_tol=1e-12):
            raise ValueError("ORIGINAL_SENTINEL_FIT_REPLAY_CHANGED_"+name)
    n_other=[int(round(math.expm1(float(x[3])))) for x in Xtest]
    return {
        "AUC_abiotic_only":scores["abiotic_only"],
        "AUC_effort_only":scores["effort_only"],
        "AUC_abiotic_plus_otherplant_effort":scores["abiotic_plus_other_plant_effort"],
        "increment_AUC_environment_beyond_effort_only":
            scores["abiotic_plus_other_plant_effort"]-scores["effort_only"],
        "conditional_same_exact_effort_abiotic_only":conditional_auc(
             list(ytest),ranks["abiotic_only"],n_other,binned=False),
        "conditional_same_exact_effort_abiotic_plus_effort":conditional_auc(
             list(ytest),ranks["abiotic_plus_other_plant_effort"],n_other,binned=False),
        "conditional_fixed_bins_abiotic_only":conditional_auc(
             list(ytest),ranks["abiotic_only"],n_other,binned=True),
        "conditional_fixed_bins_abiotic_plus_effort":conditional_auc(
             list(ytest),ranks["abiotic_plus_other_plant_effort"],n_other,binned=True),
        "source_effort_proxy_is_not_independently_measured":True,
    }


def replay_three(plant_cells,rasters,countries,prior):
    from pyproj import Transformer
    data=pilot.country_cell_taxa(plant_cells)
    heldout=pilot.HOLDOUT
    # Exactly same country-cell leakage prevention as original.
    banned=set(data[heldout])
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    cache={}
    originals={x["plant"]:x for x in prior["plants"]}
    rows=[]
    for focal in pilot.SENTINELS:
        train_labeled=[]
        for cc in countries:
            if cc==heldout:continue
            train_labeled.extend(pilot.make_labeled_cells(
                 data,focal,cc,excluded_cells=banned))
        test_labeled=pilot.make_labeled_cells(data,focal,heldout)
        train,trainmissing=pilot.dataframe_rows(train_labeled,rasters,xfm,cache)
        test,testmissing=pilot.dataframe_rows(test_labeled,rasters,xfm,cache)
        a=originals[focal]
        npos=sum(int(y) for y,x in train)
        tpos=sum(int(y) for y,x in test)
        if (npos!=a["train_positive_recorded_25km_cells"] or
            len(train)-npos!=a["train_other_plant_target_background_cells"] or
            tpos!=a["test_positive_recorded_25km_cells"] or
            len(test)-tpos!=a["test_other_plant_target_background_cells"] or
            trainmissing!=a["train_abiotic_nodata_excluded_cells"] or
            testmissing!=a["test_abiotic_nodata_excluded_cells"]):
            raise ValueError("OLD_PILOT_CELL_DENOMINATOR_DRIFT_"+focal)
        diag=model_diagnostics(train,test)
        if not math.isclose(diag["AUC_abiotic_only"],a["AUC_abiotic_only"],abs_tol=1e-12):
            raise ValueError("OLD_PILOT_ABIOTIC_AUC_DRIFT")
        if not math.isclose(diag["AUC_abiotic_plus_otherplant_effort"],
                            a["AUC_abiotic_plus_otherplant_effort"],abs_tol=1e-12):
            raise ValueError("OLD_PILOT_COMBINED_AUC_DRIFT")
        rows.append({
            "plant":focal,"holdout_country":heldout,
            "train_positive_cells":npos,"test_positive_cells":tpos,
            "test_pseudo_background_cells":len(test)-tpos,
            "all_old_cell_counts_and_AUC_replayed_exactly":True,
            "diagnostics":diag
        })
    return rows


def execute():
    pilot.verified_v2_names()
    old=read(OLD)
    if old["status"]!="EXPLORATORY_COUNTRY_EXCLUDED_3PLANT_PILOT_COMPLETE" or \
       old["heldout_country"]!=pilot.HOLDOUT or \
       old["frozen_sentinel_species"]!=list(pilot.SENTINELS):
        raise RuntimeError("ORIGINAL_FROZEN_PILOT_RESULT_CHANGED")
    source=verified_source(read(D/"gbif_download_submission.json"),
                           read(D/"gbif_download_doi_poll.json"))
    head=read(D/"gbif_archive_header_preflight.json")
    qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    countries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    with tempfile.TemporaryDirectory(prefix="neobat-plant-source-effort-diagnostic-") as temp:
        directory=pathlib.Path(temp)
        ziptarget=directory/"original_plants.zip"
        if source["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
           source["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
            raise RuntimeError("SOURCE_DOI_ROW_COUNT_DRIFT")
        receipt=safe_archive(source["plant"]["url"],ziptarget)
        if receipt["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           receipt["sha256"]!=head["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_SOURCE_PLANT_SHA_DRIFT")
        cells=strict_cell_records(ziptarget,group="plant",
            source=head["files"]["plant"],accepted=accepted["plant"],
            expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,qc)
        members,metadata=pilot.verify_raster_sources(directory)
        with ExitStack() as stack:
            rasters=pilot.open_source_rasters(stack,members)
            output=replay_three(cells,rasters,countries,old)
    if len(output)!=3:raise RuntimeError("MISSING_OR_ADDED_SENTINEL")
    return {
        "schema_version":1,
        "status":"EXPLORATORY_POSTHOC_PLANT_EFFORT_DIAGNOSTIC_COMPLETE",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "previous_result":OLD,
        "source_DOI":EXPECTED["plant"]["doi"],
        "source_archive_sha256":receipt["sha256"],
        "worldclim_source_sha256":metadata["climate_zip_sha256"],
        "elevation_source_sha256":metadata["elevation_zip_sha256"],
        "frozen_sentinels":list(pilot.SENTINELS),
        "all_old_pilot_results_exactly_replayed":True,
        "results_are_posthoc_and_exploratory":True,
        "study_effort_independently_measured":False,
        "no_bat_model_M1_M3_N1_fitted":True,
        "M3_minus_M1_bat_auc":None,
        "raw_coords_or_plant_records_saved":False,
        "plants":output
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_effort_confounding_diagnostic.json")
    a=p.parse_args();out=pathlib.Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try: result=execute()
    except Exception as exc:
        result={
            "schema_version":1,"status":"POSTHOC_PLANT_EFFORT_DIAGNOSTIC_STOP",
            "error_type":type(exc).__name__,"error_code":str(exc)[:220],
            "M3_minus_M1_bat_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_PLANT_EFFORT_DIAGNOSTIC",result["status"],flush=True)
    for item in result.get("plants",[]):
        d=item["diagnostics"]
        print("PLANT",item["plant"],"AUC_abiotic",d["AUC_abiotic_only"],
              "AUC_effort",d["AUC_effort_only"],
              "AUC_combined",d["AUC_abiotic_plus_otherplant_effort"],
              "delta",d["increment_AUC_environment_beyond_effort_only"],flush=True)
    return 0 if result["status"]=="EXPLORATORY_POSTHOC_PLANT_EFFORT_DIAGNOSTIC_COMPLETE" else 3


if __name__=="__main__":
    raise SystemExit(main())
