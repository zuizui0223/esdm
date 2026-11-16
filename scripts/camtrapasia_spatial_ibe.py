#!/usr/bin/env python3
"""C1: once-only independent Asian mammal community IBD/IBE predictive check.

Frozen in docs/replication/CAMTRAPASIA_SPATIAL_IBE_FROZEN_DESIGN.md before
capture table was opened. This is NOT E5, eSDM-fitting, a causal test, or a
camera-specific effort/detection model.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import median, mean, pstdev

EXPECTED_MD5 = {
    'metadata': '2b50c534737b0c98a93da54128b10a32',
    'captures': 'a73975d7626def4012a4e1197497ba87',
    'traits': '59e0748f8aaf59b23b936248f1e63fc9',
}
ENV = ('forest_cover_20km', 'precipitation_20km',
       'temperature_20km', 'human_footprint_20km')
META_REQUIRED = ('survey_id', 'country', 'landscape', 'effort', 'n_cameras',
                 'Y_lat', 'X_long', 'Source') + ENV
CAP_REQUIRED = ('survey_id', 'records', 'class', 'binomial_verified', 'taxonomic_level')
ALPHA = 5.0


def digest(path: Path, algo: str = 'md5') -> str:
    h = hashlib.new(algo)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def finite(value):
    try:
        f = float(value)
        return f if math.isfinite(f) else None
    except (ValueError, TypeError):
        return None


def read_metadata(path: Path):
    allrows = {}
    excluded = Counter()
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(META_REQUIRED).issubset(set(reader.fieldnames or [])):
            raise ValueError('METADATA_SCHEMA_STOP: required metadata columns missing')
        for r in reader:
            key = r['survey_id'].strip()
            if not key or key in allrows:
                raise ValueError('METADATA_SCHEMA_STOP: blank/duplicate survey_id')
            allrows[key] = r
    good = {}
    for key, row in allrows.items():
        nums = {x: finite(row[x]) for x in ('effort','n_cameras','Y_lat','X_long')+ENV}
        if any(n is None for n in nums.values()):
            excluded['missing_nonfinite'] += 1; continue
        if nums['effort'] < 500 or nums['n_cameras'] < 10:
            excluded['effort_camera_threshold'] += 1; continue
        if not (-90 <= nums['Y_lat'] <= 90 and -180 <= nums['X_long'] <= 180):
            excluded['bad_geography'] += 1; continue
        if not row['country'].strip() or not row['landscape'].strip():
            excluded['missing_group'] += 1; continue
        good[key] = {
            'id': key,
            'country': row['country'].strip(),
            'landscape': row['landscape'].strip(),
            'source': row['Source'].strip(),
            'effort': nums['effort'],
            'lat': nums['Y_lat'], 'lon': nums['X_long'],
            'env': tuple(nums[x] for x in ENV),
        }
    return good, {'metadata_total': len(allrows), 'metadata_eligible': len(good),
                  'metadata_excluded': dict(excluded)}


def read_capture_sets(path: Path, survey_ids: set[str]):
    records = defaultdict(Counter)
    exclusions = Counter()
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(CAP_REQUIRED).issubset(set(reader.fieldnames or [])):
            raise ValueError('RESPONSE_SCHEMA_STOP: captures required columns missing')
        for r in reader:
            exclusions['total_rows'] += 1
            study = r['survey_id'].strip()
            if study not in survey_ids:
                exclusions['not_eligible_study'] += 1; continue
            if r['class'].strip().lower() != 'mammalia':
                exclusions['not_mammal'] += 1; continue
            if r['taxonomic_level'].strip().lower() != 'species':
                exclusions['not_species'] += 1; continue
            name = ' '.join(r['binomial_verified'].strip().split())
            if len(name.split(' ')) != 2:
                exclusions['not_binomial'] += 1; continue
            n = finite(r['records'])
            if n is None or n < 0 or n != int(n):
                exclusions['not_integer_independent_records'] += 1; continue
            records[study][name] += int(n)
            exclusions['qualified_mammal_rows'] += 1
    seen = {k:{species for species, count in sums.items() if count >= 2}
            for k,sums in records.items()}
    return seen, dict(exclusions)


def split_group(row):
    token = f'C1-20261117|{row["country"]}|{row["landscape"]}'
    return 'validation' if hashlib.sha256(token.encode()).digest()[0] < 51 else 'discovery'


def haversine(a, b):
    la1, lo1 = map(math.radians, (a['lat'],a['lon']))
    la2, lo2 = map(math.radians, (b['lat'],b['lon']))
    dlat, dlon = la2-la1, lo2-lo1
    t = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlon/2)**2
    return 6371.0088*2*math.asin(math.sqrt(min(1.0,max(0.0,t))))


def beta_sim(x, y):
    a = len(x & y)
    b, c = len(x - y), len(y - x)
    return min(b,c)/(a+min(b,c)) if a+min(b,c)>0 else None


def center_scale(values):
    avg = mean(values)
    sd = pstdev(values)
    return avg, sd if sd > 1e-12 else 1.0


def environmental_scale(studies):
    centers = [center_scale([s['env'][i] for s in studies]) for i in range(4)]
    # A constant feature must contribute EXACTLY zero for all studies.
    for j in range(4):
        if len(set(s['env'][j] for s in studies)) <= 1:
            centers[j] = (centers[j][0], None)
    return centers


def pair_features(a, b, centers):
    d = math.log1p(haversine(a,b))
    effort = abs(math.log(a['effort']/b['effort']))
    env = math.sqrt(sum(((a['env'][i]-b['env'][i])/sd)**2
                        for i,(_,sd) in enumerate(centers) if sd is not None))
    return [d, effort, env]


def pairs_for(studies, sets, centers):
    out = []
    for a,b in combinations(studies,2):
        target = beta_sim(sets[a['id']],sets[b['id']])
        if target is not None:
            out.append({'y': target,'x': pair_features(a,b,centers),
                        'same_country': a['country']==b['country']})
    return out


def solve_linear(A, b):
    """Deterministic Gauss-Jordan for tiny positive-definite ridge Gram matrices."""
    n = len(b)
    tab = [[float(z) for z in A[i]]+[float(b[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col,n),key=lambda i:abs(tab[i][col]))
        if abs(tab[pivot][col])<1e-12:
            raise ValueError('MODEL_SINGULAR_STOP')
        tab[col],tab[pivot] = tab[pivot],tab[col]
        val = tab[col][col]
        tab[col] = [v/val for v in tab[col]]
        for i in range(n):
            if i==col: continue
            factor=tab[i][col]
            tab[i] = [v-factor*w for v,w in zip(tab[i],tab[col])]
    return [tab[i][-1] for i in range(n)]


def ridge_fit(training, use_env: bool):
    k = 3 if use_env else 2
    xmean, xsd = [], []
    for j in range(k):
        m,s = center_scale([r['x'][j] for r in training])
        xmean.append(m); xsd.append(s)
    ymean = mean(r['y'] for r in training)
    X = [[(r['x'][j]-xmean[j])/xsd[j] for j in range(k)] for r in training]
    y = [r['y']-ymean for r in training]
    gram = [[sum(x[i]*x[j] for x in X)+(ALPHA if i==j else 0)
             for j in range(k)] for i in range(k)]
    rhs = [sum(x[i]*yval for x,yval in zip(X,y)) for i in range(k)]
    coeff = solve_linear(gram,rhs)
    return {'intercept':ymean,'coef':coeff,'xmean':xmean,'xsd':xsd,
            'alpha':ALPHA,'predictors':['geography','effort']+(['environment'] if use_env else [])}


def predict(fit, r):
    raw=fit['intercept']+sum(c*(r['x'][i]-fit['xmean'][i])/fit['xsd'][i]
                              for i,c in enumerate(fit['coef']))
    return min(1,max(0,raw))


def score(fit, rows):
    return mean(abs(r['y']-predict(fit,r)) for r in rows) if rows else None


def summary_pairs(rows):
    return {'pair_count':len(rows),
            'median_beta_sim':median(r['y'] for r in rows) if rows else None,
            'fraction_beta_sim_positive':sum(r['y']>0 for r in rows)/len(rows) if rows else None,
            'median_geo_distance_km':median(math.expm1(r['x'][0]) for r in rows) if rows else None,
            'median_environmental_distance':median(r['x'][2] for r in rows) if rows else None}


def analyze(metadata, captures):
    available={k:v for k,v in metadata.items() if len(captures.get(k,set()))>=5}
    grouped={'discovery':[], 'validation':[]}
    for row in available.values():
        grouped[split_group(row)].append(row)
    d,v=(sorted(grouped[name],key=lambda x:x['id']) for name in ('discovery','validation'))
    n_land=lambda rows:len({(r['country'],r['landscape']) for r in rows})
    support={'discovery_studies':len(d),'validation_studies':len(v),
             'discovery_landscapes':n_land(d),'validation_landscapes':n_land(v)}
    if (len(d)<30 or len(v)<12 or n_land(d)<8 or n_land(v)<4):
        return {'status':'INSUFFICIENT_TRANSFER_SUPPORT','support':support,
                'interpretation':'Predeclared study/landscape minima not reached; no outcome-based rescue'}
    centers=environmental_scale(d)
    dp, vp = pairs_for(d,captures,centers),pairs_for(v,captures,centers)
    support.update({'discovery_pairs':len(dp),'validation_pairs':len(vp)})
    if min(len(dp),len(vp))<100:
        return {'status':'INSUFFICIENT_TRANSFER_SUPPORT','support':support,
                'interpretation':'Predeclared pair support below 100 in a partition'}
    base, full=ridge_fit(dp,False),ridge_fit(dp,True)
    error_base=score(base,vp)
    error_full=score(full,vp)
    gain=error_base-error_full
    secondary={}
    for group in ('same_country','different_country'):
        rows=[r for r in vp if r['same_country']==(group=='same_country')]
        secondary[group]={'heldout_pairs':len(rows), 'mae_gain':score(base,rows)-score(full,rows)
                          if len(rows)>=20 else None,
                          'status':'ESTIMABLE' if len(rows)>=20 else 'INSUFFICIENT_PAIR_SUPPORT'}
    discovery_sources={s['source'] for s in d if s['source']}
    validation_sources={s['source'] for s in v if s['source']}
    return {'status':'C1_EVALUATED_POSITIVE' if gain>=.02 and full['coef'][2]>0 else 'C1_EVALUATED_NO_INCREMENTAL_PREDICTIVE_EVIDENCE',
            'support':support,
            'primary':{'mae_geography_effort_only':error_base,
                       'mae_geography_effort_environment':error_full,
                       'heldout_mae_gain_baseline_minus_full':gain,
                       'train_environment_coefficient_standardized':full['coef'][2],
                       'positive_rule_mae_0_02_and_positive_environment_coefficient':gain>=.02 and full['coef'][2]>0,
                       'fit_base':base,'fit_full':full},
            'pair_descriptives':{'discovery':summary_pairs(dp),'validation':summary_pairs(vp)},
            'secondary':secondary,
            'overlap':{'shared_named_sources_discovery_validation':len(discovery_sources&validation_sources),
                       'distinct_source_names_discovery':len(discovery_sources),
                       'distinct_source_names_validation':len(validation_sources)},
            'inference_limits':{'pairwise_rows_not_independent':True,
                                'not_formal_CI_or_p_value':True,
                                'not_detection_calibrated':True,
                                'not_eSDM_model_fit':True,
                                'not_confirmation_of_Safari14_mechanism':True}}


def run(metadata:Path,captures:Path,traits:Path):
    files={'metadata':metadata,'captures':captures,'traits':traits}
    md5={k:digest(p) for k,p in files.items()}
    for k, h in md5.items():
        if h!=EXPECTED_MD5[k]:
            raise ValueError(f'TRANSPORT_OR_SOURCE_STOP: {k} MD5 mismatch')
    meta, quality = read_metadata(metadata)
    captured, extra = read_capture_sets(captures,set(meta))
    result=analyze(meta,captured)
    result.update({'schema_version':1,'date':'2026-11-17','source':{'doi':'10.5281/zenodo.10780971',
             'file_md5':md5,'file_sha256':{k:digest(v,'sha256') for k,v in files.items()}},
             'quality':quality|{'captures':extra,
              'response_eligible_studies_atleast_five_species':sum(len(v)>=5 for v in captured.values()),
              'domestic_category_not_excluded_per_frozen_design':True},
             'frozen_design':'docs/replication/CAMTRAPASIA_SPATIAL_IBE_FROZEN_DESIGN.md'})
    return result


def main():
    parser=argparse.ArgumentParser()
    for field in ('metadata','captures','traits','out'):
        parser.add_argument('--'+field,required=True,type=Path)
    args=parser.parse_args()
    result=run(args.metadata,args.captures,args.traits)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'support':result['support'],
                      'primary':result.get('primary',{}).get('heldout_mae_gain_baseline_minus_full')},sort_keys=True))

if __name__=='__main__':main()