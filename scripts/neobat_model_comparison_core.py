"""NeoBat M0/M1/M2/M3/N1 country-heldout relative-rank benchmark core.

This implements a *model comparison* only when independently prepared
bat/background events, outcountry cross-fitted plant relative suitabilities,
and source-audited links are provided. It does not retrieve rasters or
interpret background as absence. A synthetic flag permanently labels tests.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

EXPECTED_BAT_DOI="10.15468/dl.nxu727"
EXPECTED_PLANT_DOI="10.15468/dl.xwc5zf"
ENV=("temperature","precipitation","forest","topography","effort")

class QualificationStop(ValueError):
    pass

def rank_auc(labels, scores):
    if len(labels)!=len(scores) or not labels:
        raise QualificationStop("AUC_LENGTH_OR_EMPTY")
    if any(y not in (0,1) for y in labels):
        raise QualificationStop("AUC_INVALID_LABEL")
    p=sum(labels)
    n=len(labels)-p
    if p==0 or n==0:
        raise QualificationStop("AUC_NEEDS_PRESENCE_AND_TARGET_BACKGROUND")
    if any(not math.isfinite(float(s)) for s in scores):
        raise QualificationStop("NONFINITE_PREDICTION")
    ordered=sorted(zip(map(float,scores),labels))
    rank_sum=0.0
    i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered) and ordered[j][0]==ordered[i][0]:
            j+=1
        avg_rank=(i+1+j)/2.0
        rank_sum+=avg_rank*sum(y for _,y in ordered[i:j])
        i=j
    return (rank_sum-p*(p+1)/2.0)/(p*n)

def _numeric(v,field):
    try: x=float(v)
    except (TypeError,ValueError):
        raise QualificationStop("INVALID_NUMERIC_"+field)
    if not math.isfinite(x):
        raise QualificationStop("NONFINITE_"+field)
    return x

def _bool(v):
    return v is True or str(v).lower()=="true"

def _training_links(links,holdout,plant_universe,site_reference_embargo):
    """Embargo all original NeoBat site references from heldout country.

    The embargo MUST come from the complete original sites table, not just
    retained frugivory links: an omitted plant or guild can still share a
    publication with an included plant from another country.
    """
    if not isinstance(site_reference_embargo,(list,tuple,set)):
        raise QualificationStop("MISSING_FULL_SITE_REFERENCE_EMBARGO")
    if any(not isinstance(v,str) or not v.strip() for v in site_reference_embargo):
        raise QualificationStop("INVALID_FULL_SITE_REFERENCE_EMBARGO")
    banned=set(site_reference_embargo)
    if len(banned)!=len(site_reference_embargo):
        raise QualificationStop("DUPLICATE_SITE_REFERENCE_EMBARGO")
    if any(not r.get("ref_id") or not r.get("bat") for r in links):
        raise QualificationStop("MISSING_SOURCE_LINK_REFERENCE")
    linked_in_holdout={r["ref_id"] for r in links if r["source_country"]==holdout}
    if not linked_in_holdout.issubset(banned):
        raise QualificationStop("INCOMPLETE_SITE_REFERENCE_EMBARGO")
    rows=[r for r in links if r.get("source_country")!=holdout
          and r["ref_id"] not in banned and r["plant"] in plant_universe]
    return rows,banned

def _network_edges(links):
    return sorted({(r["bat"],r["plant"]) for r in links})

def _is_rewirable(edges):
    e=set(edges)
    for i,(a,p) in enumerate(edges):
        for b,q in edges[i+1:]:
            if a!=b and p!=q and (a,q) not in e and (b,p) not in e:
                return True
    return False

def degree_preserving_rewire(edges,rng,attempts):
    """Markov-chain bipartite edge swaps; same bat and plant degrees."""
    current=list(edges)
    present=set(current)
    changed=0
    for _ in range(attempts):
        if len(current)<2:break
        i,j=rng.sample(range(len(current)),2)
        a,p=current[i]
        b,q=current[j]
        if a==b or p==q or (a,q) in present or (b,p) in present:continue
        present.remove((a,p))
        present.remove((b,q))
        present.add((a,q))
        present.add((b,p))
        current[i]=(a,q)
        current[j]=(b,p)
        changed+=1
    return current,changed

def _validate_manifest(manifest,plant_universe,holdout):
    if holdout not in manifest.get("outer_holdout_regions",[]):
        raise QualificationStop("HOLDOUT_NOT_PREDECLARED")
    if len(set(plant_universe))!=len(plant_universe) or len(plant_universe)<3:
        raise QualificationStop("INVALID_FIXED_PLANT_UNIVERSE")
    embargoes=manifest.get("site_reference_embargo_by_holdout")
    if not isinstance(embargoes,dict) or holdout not in embargoes:
        raise QualificationStop("NO_ORIGINAL_SITE_REFERENCE_EMBARGO_BY_HOLDOUT")
    synthetic=_bool(manifest.get("synthetic",False))
    if not synthetic:
        if manifest.get("bat_GBIF_DOI")!=EXPECTED_BAT_DOI or manifest.get("plant_GBIF_DOI")!=EXPECTED_PLANT_DOI:
            raise QualificationStop("MISSING_OR_CHANGED_GBIF_DOI")
        if len(plant_universe)!=255:
            raise QualificationStop("FULL_PLANT_COHORT_REQUIRED")
        for name in ("environment_source_sha256","bat_source_sha256","plant_source_sha256",
                     "sampling_bias_reference_id","frozen_holdout_receipt_sha256"):
            h=manifest.get(name)
            if not isinstance(h,str) or len(h)<12:
                raise QualificationStop("MISSING_PROVENANCE_"+name)
    return synthetic

def _plant_scores(rows,plants,universe,holdout):
    p={}
    for r in plants:
        if r["holdout_region"]!=holdout:
            continue
        if not _bool(r.get("excluded_from_plant_training")):
            raise QualificationStop("PLANT_TRAINING_CONTAINS_HELDOUT_REGION")
        cell=r["cell_id"]
        name=r["plant"]
        if name not in universe:
            raise QualificationStop("PLANT_PREDICTOR_OUTSIDE_FROZEN_UNIVERSE")
        score=_numeric(r["relative_suitability"],"relative_suitability")
        if not 0<=score<=1:
            raise QualificationStop("PLANT_SCORE_NOT_RELATIVE_ZERO_ONE")
        key=(cell,name)
        if key in p:raise QualificationStop("DUPLICATE_PLANT_CELL_FOLD")
        p[key]=score
    expected={(r["cell_id"],plant) for r in rows for plant in universe}
    if set(p)!=expected:
        raise QualificationStop("INCOMPLETE_PLANT_CROSS_FITTED_GRID")
    return p

def _arrays(rows,universe,plants,partners,holdout):
    # all plant features are one heldout-region cross-fitted model, for
    # training *and* test bat rows (no plant occurrence from test region).
    feats=[]
    labels=[]
    for r in rows:
        cell=r["cell_id"]
        env=[_numeric(r.get(col),col) for col in ENV]
        b=sum(plants[cell,s] for s in universe)/len(universe)
        resource=sum(plants[cell,s] for s in partners)/len(partners)
        feats.append(env+[b,resource])
        labels.append(1 if r["role"]=="presence" else 0)
    return feats,labels

def _ridge_logit_auc(xtr,ytr,xte,yte,features,reg=1.0):
    try:
        import numpy as np
    except ImportError as exc:
        raise QualificationStop("NUMPY_REQUIRED_FOR_MODEL_FIT") from exc
    train=np.asarray([[float(a[j]) for j in features] for a in xtr],dtype=float)
    test=np.asarray([[float(a[j]) for j in features] for a in xte],dtype=float)
    y=np.asarray(ytr,dtype=float)
    if len(np.unique(y))!=2:
        raise QualificationStop("TRAIN_NEEDS_BOTH_CLASSES")
    mean=train.mean(axis=0)
    sd=train.std(axis=0)
    sd=np.where(sd<1e-12,1.,sd)
    train=(train-mean)/sd
    test=(test-mean)/sd
    tr=np.column_stack((np.ones(len(train)),train))
    te=np.column_stack((np.ones(len(test)),test))
    beta=np.zeros(tr.shape[1])
    mask=np.ones(len(beta));mask[0]=0.
    for _ in range(80):
        z=np.clip(tr @ beta,-30,30)
        pred=1/(1+np.exp(-z))
        w=np.maximum(pred*(1-pred),1e-8)
        gradient=tr.T @ (y-pred)-reg*mask*beta
        hessian=tr.T@(w[:,None]*tr)+reg*np.diag(mask)
        hessian[0,0]+=1e-7
        step=np.linalg.solve(hessian,gradient)
        if not np.all(np.isfinite(step)):
            raise QualificationStop("LOGISTIC_SOLVE_NONFINITE")
        beta+=np.clip(step,-2,2)
        if np.max(np.abs(step))<1e-6:break
    scores=te @ beta
    return rank_auc(yte,list(scores)),len(ytr),len(yte)

def compare_fold(records,plants,links,manifest,bat,holdout,*,null_draws=199,seed=20261119):
    universe=tuple(manifest.get("plant_universe",[]))
    synthetic=_validate_manifest(manifest,universe,holdout)
    focal=[r for r in records if r.get("bat")==bat]
    if not focal:
        raise QualificationStop("FOCAL_BAT_NOT_IN_RESPONSE")
    if any(r.get("role") not in ("presence","target_background") for r in focal):
        raise QualificationStop("BACKGROUND_IS_NOT_VERIFIED_ABSENCE")
    if any(not r.get("source_event_id") or not r.get("source_dataset_key") for r in focal):
        raise QualificationStop("MISSING_SOURCE_EVENT_OR_DATASET")
    events=[r["source_event_id"] for r in focal]
    if len(events)!=len(set(events)):
        raise QualificationStop("DUPLICATE_SOURCE_EVENT_ACROSS_FOLDS_OR_ROLES")
    training=[r for r in focal if r["region"]!=holdout]
    testing=[r for r in focal if r["region"]==holdout]
    if not training or not testing:
        raise QualificationStop("EMPTY_COUNTRY_HOLDOUT")
    if {r["cell_id"] for r in training}&{r["cell_id"] for r in testing}:
        raise QualificationStop("OVERLAPPING_TRAIN_TEST_CELLS")
    tr=[int(r["role"]=="presence") for r in training]
    te=[int(r["role"]=="presence") for r in testing]
    min_train=4 if synthetic else 20
    min_test=2 if synthetic else 5
    if min(sum(tr),len(tr)-sum(tr))<min_train or min(sum(te),len(te)-sum(te))<min_test:
        raise QualificationStop("TRAIN_OR_HELDOUT_CLASS_DENOMINATOR_STOP")
    predictors=_plant_scores(focal,plants,set(universe),holdout)
    train_links,banned=_training_links(links,holdout,set(universe),
                                           manifest["site_reference_embargo_by_holdout"][holdout])
    partners=sorted({r["plant"] for r in train_links if r["bat"]==bat})
    unique_refs={r["ref_id"] for r in train_links if r["bat"]==bat}
    if len(partners)<3 or len(unique_refs)<2:
        raise QualificationStop("TOO_FEW_OUTCOUNTRY_FRUIT_PARTNERS_OR_SOURCES")
    xtr,ytr=_arrays(training,universe,predictors,partners,holdout)
    xte,yte=_arrays(testing,universe,predictors,partners,holdout)
    auc={}
    # M2 is an explicitly secondary decomposition (M0 + observed partner
    # resource index). The frozen primary contrasts remain M3 vs M1/N1.
    for k,features in {"M0":tuple(range(5)),"M1":tuple(range(6)),
                       "M2":tuple(range(5))+(6,),"M3":tuple(range(7))}.items():
        auc[k],_,_=_ridge_logit_auc(xtr,ytr,xte,yte,features)
    base_edges=_network_edges(train_links)
    if not _is_rewirable(base_edges):
        raise QualificationStop("DEGREE_PRESERVING_NETWORK_NULL_NOT_IDENTIFIABLE")
    rng=random.Random(seed)
    null=[]
    null_partner_sets=set()
    null_original_partner_draws=0
    current=list(base_edges)
    # Fixed burn-in and move attempts; no adaptive stopping based on scores.
    current,steps=degree_preserving_rewire(current,rng,100*len(current))
    if steps==0:
        raise QualificationStop("DEGREE_REWIRE_BURNIN_FAILED")
    for rep in range(null_draws):
        current,steps=degree_preserving_rewire(current,rng,20*len(current))
        npartners=sorted(p for s,p in current if s==bat)
        null_partner_sets.add(tuple(npartners))
        if npartners==partners:
            null_original_partner_draws+=1
        if len(npartners)!=len(partners):
            raise QualificationStop("DEGREE_PRESERVATION_FAILED")
        ntr,_=_arrays(training,universe,predictors,npartners,holdout)
        nte,_=_arrays(testing,universe,predictors,npartners,holdout)
        a,_,_=_ridge_logit_auc(ntr,ytr,nte,yte,tuple(range(7)))
        null.append(a)
    # Network swaps elsewhere do not constitute an identity null for the
    # focal bat unless its own partner identities actually vary.
    if null_partner_sets=={tuple(partners)}:
        raise QualificationStop("NULL_FOCAL_LINK_IDENTITIES_INVARIANT")
    nm=sum(null)/len(null)
    return {
        "schema_version":1,
        "status":"SYNTHETIC_ONLY" if synthetic else "EXPLORATORY_DOI_BACKED_MODEL_FOLD",
        "bat":bat,"heldout_region":holdout,
        "GBIF_bat_DOI":manifest.get("bat_GBIF_DOI"),
        "GBIF_plant_DOI":manifest.get("plant_GBIF_DOI"),
        "plant_universe_size":len(universe),
        "trained_fruit_partner_names":len(partners),
        "trained_fruit_source_references":len(unique_refs),
        "source_references_excluded_due_to_holdout":len(banned),
        "training_events":len(training),"heldout_events":len(testing),
        "presence_rank_auc":auc,
        "heldout_M3_minus_M1":auc["M3"]-auc["M1"],
        "secondary_M2_minus_M0":auc["M2"]-auc["M0"],
        "secondary_M3_minus_M2":auc["M3"]-auc["M2"],
        "rewired_N1_auc_mean":nm,
        "M3_minus_rewired_N1_mean":auc["M3"]-nm,
        "rewire_p_upper_tail":(1+sum(x>=auc["M3"] for x in null))/(len(null)+1),
        "rewire_draws":len(null),
        "N1_distinct_focal_partner_sets":len(null_partner_sets),
        "N1_draws_with_unchanged_focal_partners":null_original_partner_draws,
        "background_is_not_true_absence":True,
        "plant_predictions_are_relative_not_probability":True,
        "source_country_heldout_not_unopened_independent_confirmation":True if not synthetic else None,
        "causal_interaction_established":False
    }
