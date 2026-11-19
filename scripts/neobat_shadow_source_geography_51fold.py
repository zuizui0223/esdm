"""NeoBat SHADOW S0/S1/S3/SN1 country heldout model on *source geography*.

This is a weaker exploratory *recording-geometry* test, NOT the frozen
255-species primary ecological M0/M1/M3/N1. Plant predictors are all
climate-derived source-match pseudo-background logistic scores. No forest,
independently measured survey effort, fruiting/abundance, feeding or true
absences. Raw locations, model scores, raster values and datasets stay in RAM.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import tempfile
from collections import defaultdict
from contextlib import ExitStack
from datetime import datetime,timezone

from scripts import neobat_plant_country_crossfit_pilot as plant
from scripts import neobat_plant_within_dataset_source_gate as psource
from scripts import neobat_bat_targetgroup_background_gate as bsource
from scripts import neobat_model_comparison_core as core
from scripts import neobat_plant_106x17_intensity_diagnostic as intensity
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import (
    strict_cell_records,validate_against_full_qc,links_from_author_tables)
from scripts.neobat_summarize_full_source_qc import EXPECTED
from scripts.neobat_gbif_metadata_preflight import read_source

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_SHADOW_CLIMATE_ONLY_51FOLD_FROZEN_20261119.md"
SOURCE_ELIGIBILITY=D/"full106_raster_trainability_gate.json"
OLD_PLANT_COUNTS=D/"plant_106x17_source_effort_transfer.json"
N_NULL=99
SEED=20261119
STATUS_OK="EXPLORATORY_SHADOW_SOURCE_GEOGRAPHY_COMPARE_ONLY"
STATUS_PRE="ORIGINAL_FROZEN_SOURCE_INPUT_STOP"
STATUS_PLANT="SHADOW_COUNTRY_106_PLANT_TRAINING_STOP"
STATUS_BAT="SHADOW_BAT_HELDOUT_BACKGROUND_OR_RASTER_STOP"
STATUS_NULL="SHADOW_FOCAL_SOURCE_REWIRE_NOT_IDENTIFIABLE"


def read(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def plant_fit_rows(name,holdout,country_source_rows,observed_cells,environment,previous):
    """Use same recording-process population as frozen 106x17 botanical audit."""
    train=[]
    heldout_cells=observed_cells.get(holdout,set())
    for country,rows in country_source_rows[name].items():
        if country==holdout:continue
        for cell,label,env in rows:
            if cell not in heldout_cells:
                train.append((label,env))
    npos=sum(int(y) for y,_ in train)
    nbg=len(train)-npos
    if npos!=previous["train_source_matched_focal_cells"] or \
       nbg!=previous["train_source_matched_target_background_cells"]:
        raise RuntimeError("SHADOW_ORIGINAL_BOTANICAL_TRAIN_SOURCE_COUNTS_DRIFT")
    if min(npos,nbg)<20:
        raise RuntimeError("SHADOW_PLANT_COUNTRY_TRAIN_QUANTITY_STOP")
    return train,npos,nbg


def train_source_plant_model(rows):
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    x=np.asarray([v for _,v in rows],dtype=float)
    y=np.asarray([int(a) for a,_ in rows],dtype=int)
    if x.ndim!=2 or x.shape[1]!=3 or len(set(y))!=2 or not np.all(np.isfinite(x)):
        raise RuntimeError("SHADOW_PLANT_SOURCE_FIT_FEATURE_STOP")
    norm=StandardScaler().fit(x)
    model=LogisticRegression(C=1.0,class_weight="balanced",max_iter=400,
                              solver="lbfgs",random_state=SEED)
    model.fit(norm.transform(x),y)
    return norm,model


def prepare_source_plant_rows(cells,selected,countries,rasters):
    """Original dataset-matched plant cells, screened against climate and ELEV."""
    from pyproj import Transformer
    taxa=plant.country_cell_taxa(cells)
    dataset=psource.country_dataset_cells(cells)
    xfm=Transformer.from_crs("EPSG:6933","EPSG:4326",always_xy=True)
    envcache={}
    country_cells={c:set(cs) for c,cs in taxa.items()}
    source_rows={}
    for name in selected:
        source_rows[name]={}
        for country in countries:
            ps,bg,_=psource.source_matched_country(name,country,cells,dataset)
            # Exactly the matched observed source population, requiring
            # at least one other plant in same cell in BOTH roles.
            raw=[]
            local=taxa.get(country,{})
            for cell in ps:
                other=len(local.get(cell,set()))-int(name in local.get(cell,set()))
                if other>0:
                    raw.append((cell,1))
            for cell in bg:
                source_taxa=local.get(cell,set())
                if name in source_taxa:
                    raise RuntimeError("SHADOW_PLANT_FOCAL_IN_BACKGROUND")
                if source_taxa:
                    raw.append((cell,0))
            if len({x[0] for x in raw})!=len(raw):
                raise RuntimeError("SHADOW_PLANT_DUPLICATE_CELL")
            clean=[]
            for cell,lab in raw:
                env=plant.extract_environment(cell,rasters,xfm,envcache)
                if env is not None:
                    clean.append((cell,lab,env))
            source_rows[name][country]=clean
    return source_rows,country_cells,xfm,envcache


def predict_relative_sources(selected,country,source_rows,country_cells,original_counts,
                             bat_cell_features):
    """Crossfit 106 plant models; no heldout botanical records used in training."""
    import numpy as np
    from scipy.special import expit
    if len(selected)!=106:raise RuntimeError("SHADOW_FULL_106_PLANT_UNIVERSE_REQUIRED")
    cell_ids=sorted(bat_cell_features)
    xbat=np.asarray([bat_cell_features[cell] for cell in cell_ids],dtype=float)
    if xbat.ndim!=2 or xbat.shape[1]!=3 or not len(cell_ids):
        raise RuntimeError("SHADOW_BAT_RASTER_INPUT_EMPTY")
    preds=np.empty((len(cell_ids),len(selected)),dtype=float)
    for col,name in enumerate(selected):
        train,_,_=plant_fit_rows(name,country,source_rows,country_cells,
                                None,original_counts[name,country])
        norm,model=train_source_plant_model(train)
        # Relative source-recording score, NOT a calibrated plant
        # presence/absence or biomass probability.
        scores=model.decision_function(norm.transform(xbat))
        preds[:,col]=expit(scores)
    if not np.all(np.isfinite(preds)) or np.any(preds<0) or np.any(preds>1):
        raise RuntimeError("SHADOW_PLANT_SCORE_OUTSIDE_0_1")
    return cell_ids,preds


def country_shadow(bat,country,bat_source,countries,bat_env,plant_pred,cell_lookup,
                   fixed_names,links,embargo):
    import numpy as np

    focus=bat_source
    holdout_cells=set(bat_source.get(country,{}))
    training=[]
    testing=[]
    for region in countries:
        positive,other=bsource.candidate_cells(bat_source,bat,region)
        target=testing if region==country else training
        for cell,y in [(c,1) for c in positive]+[(c,0) for c in other]:
            if region!=country and cell in holdout_cells:
                continue
            if cell not in bat_env:
                continue
            if cell not in cell_lookup:
                raise RuntimeError("SHADOW_MISSING_PLANT_CROSSFIT_AT_BAT_SOURCE_CELL")
            idx=cell_lookup[cell]
            values=bat_env[cell]
            target.append((y,values,idx))
    ytr=[y for y,e,i in training]
    yte=[y for y,e,i in testing]
    if min(sum(ytr),len(ytr)-sum(ytr))<20 or \
       min(sum(yte),len(yte)-sum(yte))<5:
        return {"status":STATUS_BAT,
                "train_focal_recorded_cells":sum(ytr),
                "train_target_background_cells":len(ytr)-sum(ytr),
                "test_focal_recorded_cells":sum(yte),
                "test_target_background_cells":len(yte)-sum(yte)}
    banned=set(embargo[country])
    permitted=[(b,p,ref) for b,p,ref,cc in links
               if cc!=country and ref not in banned and p in fixed_names]
    partner_names=sorted({p for b,p,r in permitted if b==bat})
    partner_refs={r for b,p,r in permitted if b==bat}
    if len(partner_names)<3 or len(partner_refs)<2:
        return {"status":STATUS_PRE,"reason":"NO_THREE_OUTCOUNTRY_SOURCE_PARTNERS"}
    ix={name:i for i,name in enumerate(fixed_names)}
    partners=[ix[s] for s in partner_names]
    generic=plant_pred.mean(axis=1)
    actual=plant_pred[:,partners].mean(axis=1)
    def arrays(partner_score):
        tr=[[*e,generic[i],partner_score[i]] for y,e,i in training]
        te=[[*e,generic[i],partner_score[i]] for y,e,i in testing]
        return tr,te
    tr,te=arrays(actual)
    out={}
    for k,cols in (
        ("S0",(0,1,2)),
        ("S1",(0,1,2,3)),
        ("S3",(0,1,2,3,4))
    ):
        out[k]=core._ridge_logit_auc(tr,ytr,te,yte,cols,reg=1.0)[0]
    edges=core._network_edges([{"bat":b,"plant":p} for b,p,r in permitted])
    if not core._is_rewirable(edges):
        return {"status":STATUS_NULL,"reason":"NO_DEGREE_PRESERVING_NETWORK_SWAP"}
    rng=random.Random(SEED)
    current,_=core.degree_preserving_rewire(edges,rng,100*len(edges))
    null=[]
    distinct=set()
    for _ in range(N_NULL):
        current,_=core.degree_preserving_rewire(current,rng,20*len(edges))
        names=tuple(sorted(p for s,p in current if s==bat))
        distinct.add(names)
        if len(names)!=len(partners):
            raise RuntimeError("SHADOW_REWIRE_FOCAL_DEGREE_NOT_PRESERVED")
        score=plant_pred[:,[ix[z] for z in names]].mean(axis=1)
        ntr,nte=arrays(score)
        auc=core._ridge_logit_auc(ntr,ytr,nte,yte,(0,1,2,3,4),reg=1.0)[0]
        null.append(float(auc))
    if distinct=={tuple(partner_names)}:
        return {"status":STATUS_NULL,"reason":"FOCAL_PARTNER_SET_UNCHANGED"}
    return {
       "status":STATUS_OK,
       "train_focal_recorded_cells":sum(ytr),
       "train_target_background_cells":len(ytr)-sum(ytr),
       "test_focal_recorded_cells":sum(yte),
       "test_target_background_cells":len(yte)-sum(yte),
       "source_partner_plant_names":len(partners),
       "source_independent_publication_refs_count":len(partner_refs),
       "source_partner_names_originally_published_only":True,
       "S0_abiotic_rank_auc":float(out["S0"]),
       "S1_generic_plant_rank_auc":float(out["S1"]),
       "S3_published_partner_rank_auc":float(out["S3"]),
       "S3_minus_S1_auc":float(out["S3"]-out["S1"]),
       "SN1_mean_rewired_rank_auc":sum(null)/len(null),
       "S3_minus_SN1_mean_auc":float(out["S3"]-sum(null)/len(null)),
       "SN1_p_upper_tail":(1+sum(x>=out["S3"] for x in null))/(N_NULL+1),
       "SN1_draws":N_NULL,
       "SN1_distinct_focal_partner_sets":len(distinct),
       "relative_plant_climate_scores_are_not_true_availability":True,
       "no_original_ecological_M3_vs_M1_estimated":True
    }


def build():
    selected,holdouts=psource.fixed_names_and_countries()
    gate=read(SOURCE_ELIGIBILITY)
    if gate.get("status")!="FIXED106_PLANT_TRAINING_AFTER_RASTER_PREFIT_GATE":
        raise RuntimeError("FROZEN_51_BAT_SOURCE_GATE_MISSING")
    original=gate["all_original_84_bat_folds"]
    qualified={(x["bat"],x["holdout_country"]) for x in original
               if x["full_v2_source_and_plant_training_ready"]}
    if len(original)!=84 or len(qualified)!=51:
        raise RuntimeError("FROZEN_51_OF_84_SOURCE_GATE_CHANGED")
    universe=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")
    countries=universe["GBIF_29_country_universe"]
    if len(countries)!=29 or len(holdouts)!=17:
        raise RuntimeError("COUNTRY_SOURCE_UNIVERSE_DRIFT")
    sources=verified_source(read(D/"gbif_download_submission.json"),
                            read(D/"gbif_download_doi_poll.json"))
    meta=read(D/"gbif_archive_header_preflight.json")
    qc=read(D/"gbif_full_source_qc.json")
    names=name_map(read(D/"gbif_search_preflight.json"),
                   read(D/"plant_search_preflight.json"))
    old=read(OLD_PLANT_COUNTS)
    original_counts={(x["plant"],x["holdout_country"]):x for x in
                     old["plant_country_source_rank_results"]}
    if old.get("status")!="EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE" or \
       len(original_counts)!=1802:
        raise RuntimeError("PRIOR_PLANT_COUNTRY_RASTER_TRAIN_COUNTS_MISSING")
    with tempfile.TemporaryDirectory(prefix="neobat-shadow-recording-geometry-") as tmp:
        directory=pathlib.Path(tmp)
        inputcells={}
        for group in ("bat","plant"):
            src=sources[group]
            target=directory/(group+"_original.zip")
            got=safe_archive(src["url"],target)
            if got["sha256"]!=EXPECTED[group]["archive_sha"] or \
               got["sha256"]!=meta["files"][group]["sha256"]:
                raise RuntimeError("SHADOW_ORIGINAL_GBIF_ZIP_SHA_CHANGED_"+group)
            sourcecells=strict_cell_records(target,group=group,
                source=meta["files"][group],accepted=names[group],
                expected_count=EXPECTED[group]["n_records"])
            validate_against_full_qc(group,sourcecells,qc)
            inputcells[group]=sourcecells
        author={}
        for name in ("records","sites"):
            author[name],_=read_source(name)
        links=links_from_author_tables(
            author["records"],author["sites"],bats=set(names["bat"].values()),
            plants=set(names["plant"].values()))
        climate_bodies,climate_meta=plant.verify_raster_sources(directory)
        with ExitStack() as stack:
            raster=plant.open_source_rasters(stack,climate_bodies)
            source_rows,country_plant_cells,xfm,environment=prepare_source_plant_rows(
                inputcells["plant"],selected,countries,raster)
            bat_by_country=bsource.build_country_cells(inputcells["bat"])
            bat_union={cell for data in bat_by_country.values() for cell in data}
            bat_environment={cell:e for cell in bat_union
                if (e:=plant.extract_environment(cell,raster,xfm,environment)) is not None}
            result=[]
            by_country=defaultdict(list)
            for bat,country in qualified:
                by_country[country].append(bat)
            for country in sorted(by_country):
                # Fixed 106 plant climate-only source models, each trained
                # without any botanical sources from this withheld country.
                cells,pred=predict_relative_sources(
                    selected,country,source_rows,country_plant_cells,
                    original_counts,bat_environment)
                idx={cell:i for i,cell in enumerate(cells)}
                for bat in sorted(by_country[country]):
                    out=country_shadow(bat,country,bat_by_country,countries,
                        bat_environment,pred,idx,selected,links,
                        universe["source_reference_embargo_by_holdout"])
                    result.append({"bat":bat,"holdout_country":country,**out})
            bykey={(r["bat"],r["holdout_country"]):r for r in result}
            if set(bykey)!=qualified:
                raise RuntimeError("SHADOW_SOURCE_51_FOLDS_NOT_ACCOUNTED")
            complete=[]
            for source_row in original:
                pair=(source_row["bat"],source_row["holdout_country"])
                if pair in bykey:
                    complete.append(bykey[pair])
                else:
                    complete.append({
                        "bat":pair[0],"holdout_country":pair[1],
                        "status":STATUS_PRE,"reason":"ORIGINAL_106_OR_BAT_INPUT_GATE_NOT_MET"
                    })
    fitted=[r for r in complete if r["status"]==STATUS_OK]
    by_country=defaultdict(list)
    for row in fitted:
        by_country[row["holdout_country"]].append(row)
    countries_model=sorted(by_country)
    def mean(col,rr):
        return sum(x[col] for x in rr)/len(rr)
    summary={
        "original_source_bat_country_folds":84,
        "frozen_source_eligible_weak_shadow_folds":51,
        "shadow_model_fit_qualified":len(fitted),
        "shadow_stops_from_51":51-len(fitted),
        "full_84_folds_accounted":len(complete)==84,
        "countries_with_fit":len(countries_model),
        "source_recording_S3_minus_S1_average_over_fitted_folds":None if not fitted else mean("S3_minus_S1_auc",fitted),
        "source_recording_S3_minus_SN1_average_over_fitted_folds":None if not fitted else mean("S3_minus_SN1_mean_auc",fitted),
        "fraction_S3_gt_S1":None if not fitted else sum(x["S3_minus_S1_auc"]>0 for x in fitted)/len(fitted),
        "fraction_S3_gt_SN1_mean":None if not fitted else sum(x["S3_minus_SN1_mean_auc"]>0 for x in fitted)/len(fitted),
        "per_country":[{"country":cc,"fit_count":len(by_country[cc]),
           "mean_S3_minus_S1":mean("S3_minus_S1_auc",by_country[cc]),
           "mean_S3_minus_SN1":mean("S3_minus_SN1_mean_auc",by_country[cc])}
           for cc in countries_model],
        "original_ecological_M3_minus_M1_unestimated":True,
        "original_ecological_M3_minus_N1_unestimated":True,
        "no_biological_causal_resource_effect_identified":True
    }
    return {
      "schema_version":1,
      "status":"EXPLORATORY_SHADOW_CLIMATE_ONLY_SOURCE_GEOGRAPHY_COMPLETED",
      "created_utc":datetime.now(timezone.utc).isoformat(),
      "frozen_design":DESIGN,
      "bat_GBIF_original_DOI":EXPECTED["bat"]["doi"],
      "plant_GBIF_original_DOI":EXPECTED["plant"]["doi"],
      "bat_GBIF_original_ZIP_SHA256":EXPECTED["bat"]["archive_sha"],
      "plant_GBIF_original_ZIP_SHA256":EXPECTED["plant"]["archive_sha"],
      "worldclim_climate_source_SHA256":climate_meta["climate_zip_sha256"],
      "worldclim_elevation_source_SHA256":climate_meta["elevation_zip_sha256"],
      "fixed_106_plant_SHA256":psource.FROZEN_V2_SHA,
      "plant_source_relative_scores_not_true_plant_availability":True,
      "weak_shadow_baseline_excludes_forest_and_independent_effort":True,
      "original_bat_M3_minus_M1_auc":None,
      "original_bat_M3_minus_N1_auc":None,
      "original_plant_and_bat_coordinates_or_per_cell_scores_committed":False,
      "summary":summary,
      "folds":complete
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="build/neobat/shadow_climate_only_51fold.json")
    a=parser.parse_args();out=pathlib.Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=build()
    except Exception as exc:
        result={
           "schema_version":1,
           "status":"SHADOW_SOURCE_GEOGRAPHY_MODEL_STOP",
           "error_type":type(exc).__name__,
           "error_code":str(exc)[:260],
           "original_bat_M3_minus_M1_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_SHADOW",result["status"],flush=True)
    if "summary" in result:
        print("SHADOW_SUMMARY",json.dumps(result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]=="EXPLORATORY_SHADOW_CLIMATE_ONLY_SOURCE_GEOGRAPHY_COMPLETED" else 3


if __name__=="__main__":
    raise SystemExit(main())
