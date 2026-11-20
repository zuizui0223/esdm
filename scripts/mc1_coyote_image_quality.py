#!/usr/bin/env python3
"""MC1: once-only, source-locked, withheld-site coyote *image label* prediction.

Not camera detection calibration, independently verified animal disease status,
regional occupancy inference, or a new esdm model generation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

SOURCE_COMMIT = 'a068e2aba265551e3b29b1c3ec8c4b1f34eafcdb'
SOURCE_BLOB = 'e46697b879b55ee44b09a7d8853f66c7a9de641d'
SOURCE_SIZE = 414219
SOURCE_REPO = 'https://github.com/mfidino/coyote-mange'
SOURCE_PAPER = '10.1111/1365-2656.13515'
SPLIT_SALT = 'MC1-20261119|'
SEED = 20261119
N_BOOT = 1000
SEASONS = ('Spring', 'Summer', 'Fall', 'Winter')
REQUIRED = ('new_file_name', 'blur', 'Mange_signs_present', 'In_color',
            'Season', 'Year', 'propbodyvis', 'site')
MISSING = {'', 'NA', 'NaN', 'NAN', 'nan', 'N/A', 'None', 'null'}


def git_blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f'blob {len(data)}\0'.encode('ascii'))
    h.update(data)
    return h.hexdigest()


def check_source(data: bytes):
    if len(data) != SOURCE_SIZE or git_blob_sha(data) != SOURCE_BLOB:
        raise ValueError('SOURCE_SIGNATURE_STOP: published size/Git blob mismatch')
    return hashlib.sha256(data).hexdigest()


def numeric(value, field, allow_missing=True):
    s = value.strip()
    if s in MISSING and allow_missing:
        return None
    try:
        f = float(s)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'RESPONSE_SCHEMA_STOP: invalid {field}') from exc
    if not math.isfinite(f):
        raise ValueError(f'RESPONSE_SCHEMA_STOP: nonfinite {field}')
    return f


def flag(value, field, allow_missing=False):
    s = value.strip().lower()
    if s in {x.lower() for x in MISSING} and allow_missing:
        return None
    if s in ('1', 'true'):
        return 1
    if s in ('0', 'false'):
        return 0
    raise ValueError(f'RESPONSE_SCHEMA_STOP: invalid {field} binary flag')


def parse_source(data: bytes):
    try:
        body = data.decode('utf-8-sig')
    except UnicodeError as exc:
        raise ValueError('RESPONSE_SCHEMA_STOP: invalid UTF-8') from exc
    reader = csv.DictReader(io.StringIO(body))
    if not set(REQUIRED).issubset(set(reader.fieldnames or [])):
        raise ValueError('RESPONSE_SCHEMA_STOP: expected image, site, year, season, label, and quality fields')
    records, filenames = [], set()
    for line, row in enumerate(reader, start=2):
        filename = (row['new_file_name'] or '').strip()
        site = (row['site'] or '').strip()
        if not filename or filename in filenames or not site:
            raise ValueError('RESPONSE_SCHEMA_STOP: blank/duplicate image filename or blank site')
        filenames.add(filename)
        year = (row['Year'] or '').strip()
        if not year or not year.isdecimal():
            raise ValueError('RESPONSE_SCHEMA_STOP: invalid calendar year')
        season_raw = (row['Season'] or '').strip().lower()
        if season_raw not in {x.lower() for x in SEASONS}:
            raise ValueError('RESPONSE_SCHEMA_STOP: invalid season')
        season = next(s for s in SEASONS if s.lower() == season_raw)
        blur = numeric(row['blur'] or '', 'blur')
        body_fraction = numeric(row['propbodyvis'] or '', 'propbodyvis')
        if blur is not None and blur < 0:
            raise ValueError('RESPONSE_SCHEMA_STOP: negative blur')
        if body_fraction is not None and not (0 <= body_fraction <= 1):
            raise ValueError('RESPONSE_SCHEMA_STOP: body fraction outside [0,1]')
        rec = dict(site=site,year=int(year),season=season,
                   y=flag(row['Mange_signs_present'] or '', 'mange signs'),
                   blur=blur,body=body_fraction,
                   color=flag(row['In_color'] or '', 'photo color', allow_missing=True))
        records.append(rec)
    if not records:
        raise ValueError('RESPONSE_SCHEMA_STOP: no camera-positive image records')
    return records


def split_site(site):
    val = hashlib.sha256((SPLIT_SALT + site).encode('utf-8')).digest()[0]
    return 'validation' if val < 51 else 'discovery'


def split_records(records):
    out = {'discovery': [], 'validation': []}
    for r in records:
        out[split_site(r['site'])].append(r)
    return out


def support_check(split):
    out = {}
    for name, rows in split.items():
        sites = {r['site'] for r in rows}
        positives = sum(r['y'] == 1 for r in rows)
        out[name] = {'site_count': len(sites), 'images': len(rows),
                     'mange_sign_positive_images': positives,
                     'mange_sign_negative_images': len(rows) - positives}
    d, v = out['discovery'], out['validation']
    qualifies = (d['site_count'] >= 60 and d['images'] >= 1500 and
                 v['site_count'] >= 12 and v['images'] >= 300 and
                 all(x['mange_sign_positive_images'] >= 20 and
                     x['mange_sign_negative_images'] >= 20 for x in (d, v)))
    return out, qualifies


def _norm(values):
    avg = statistics.mean(values)
    sd = statistics.pstdev(values)
    return avg, sd if sd > 1e-12 else 1.0


def _median_nonmissing(rows, field):
    v = [r[field] for r in rows if r[field] is not None]
    return statistics.median(v) if v else 0.0


def fit_feature_encoding(train):
    from math import log1p
    med = {k: _median_nonmissing(train, k) for k in ('blur', 'body', 'color')}
    center = {}
    center['year'] = _norm([r['year'] for r in train])
    center['blur'] = _norm([log1p(r['blur'] if r['blur'] is not None else med['blur']) for r in train])
    center['body'] = _norm([r['body'] if r['body'] is not None else med['body'] for r in train])
    return {'medians': med, 'centering': center}


def features(rows, cfg, full=False):
    from math import log1p
    m = cfg['medians']
    c = cfg['centering']
    matrix = []
    for r in rows:
        year_z = (r['year'] - c['year'][0]) / c['year'][1]
        x = [year_z] + [int(r['season'] == s) for s in ('Summer', 'Fall', 'Winter')]
        if full:
            blur = log1p(r['blur'] if r['blur'] is not None else m['blur'])
            body = r['body'] if r['body'] is not None else m['body']
            color = r['color'] if r['color'] is not None else m['color']
            x.extend([(blur - c['blur'][0]) / c['blur'][1],
                      (body - c['body'][0]) / c['body'][1], color,
                      int(r['blur'] is None), int(r['body'] is None)])
        matrix.append(x)
    return matrix


def _percentile_sorted(xs, p):
    pos = (len(xs) - 1) * p
    low = int(pos)
    high = min(low + 1, len(xs) - 1)
    return xs[low] * (high - pos) + xs[high] * (pos - low) if low != high else xs[low]


def brier(y, p):
    return statistics.mean((float(a)-float(b))**2 for a,b in zip(y,p))


def logloss(y, p):
    return statistics.mean(-a*math.log(max(1e-8,min(1-1e-8, pr))) -
                           (1-a)*math.log(max(1e-8,min(1-1e-8,1-pr)))
                           for a,pr in zip(y,p))


def station_bootstrap(rows, prob0, prob1, n_boot=N_BOOT, seed=SEED):
    bins = defaultdict(lambda: [0,0.0])
    for r, p0, p1 in zip(rows, prob0, prob1):
        site = r['site']
        bins[site][0] += 1
        bins[site][1] += (r['y']-p0)**2 - (r['y']-p1)**2
    vals = list(bins.values())
    rng = random.Random(seed)
    bs = []
    for _ in range(n_boot):
        sample = [vals[rng.randrange(len(vals))] for _ in range(len(vals))]
        n = sum(x[0] for x in sample)
        bs.append(sum(x[1] for x in sample)/n)
    bs.sort()
    return [_percentile_sorted(bs, .025), _percentile_sorted(bs, .975)]


def evaluate(records):
    from sklearn.linear_model import LogisticRegression
    split = split_records(records)
    support, passes = support_check(split)
    if not passes:
        return {'status':'INSUFFICIENT_SUPPORT','support':support,
                'biological_prediction_evaluated':False}
    train, valid = split['discovery'], split['validation']
    cfg = fit_feature_encoding(train)
    y_train = [r['y'] for r in train]
    y_valid = [r['y'] for r in valid]
    def fit_predict(include_quality):
        model = LogisticRegression(C=1.0, penalty='l2', solver='lbfgs',
              max_iter=1000, tol=1e-8, class_weight=None, random_state=SEED)
        model.fit(features(train,cfg,include_quality),y_train)
        return list(model.predict_proba(features(valid,cfg,include_quality))[:,1]), model.n_iter_[0]
    p0, iter0 = fit_predict(False)
    p1, iter1 = fit_predict(True)
    err0,err1=brier(y_valid,p0),brier(y_valid,p1)
    log0,log1=logloss(y_valid,p0),logloss(y_valid,p1)
    gain=err0-err1
    ci=station_bootstrap(valid,p0,p1)
    positive=gain >= .005 and log0-log1>0 and ci[0]>0
    negative=gain <=-.005 and ci[1]<0
    return {'status':'MC1_POSITIVE_HELDOUT_IMAGE_LABEL_PREDICTION' if positive else
                     'MC1_NEGATIVE_HELDOUT_IMAGE_LABEL_PREDICTION' if negative else
                     'MC1_INCONCLUSIVE_HELDOUT_IMAGE_LABEL_PREDICTION',
            'support':support,'primary':{'brier_baseline':err0,'brier_quality':err1,
               'heldout_brier_gain':gain,'heldout_logloss_baseline':log0,
               'heldout_logloss_quality':log1,'heldout_logloss_gain':log0-log1,
               'site_cluster_bootstrap_95_interval':ci,'bootstrap_draws':N_BOOT,
               'bootstrap_seed':SEED,'model_n_iter':[int(iter0),int(iter1)]},
            'biological_prediction_evaluated':True,
            'limits':{'camera_positive_images_only':True,'true_mange_status_unverified':True,
                'site_bootstrap_not_spatial_autocorrelation_calibrated':True,
                'not_E5_G4':True,'not_camera_miss_detection_probability':True,
                'not_ecological_causal_or_esdm_superiority':True}}


def run(path:Path):
    raw=path.read_bytes()
    digest=check_source(raw)
    rows=parse_source(raw)
    result=evaluate(rows)
    result.update({'schema_version':1,'date':'2026-11-19',
         'source':{'article_doi':SOURCE_PAPER,'repository_commit':SOURCE_COMMIT,
                   'source_file':'data/coydata_merged_sites.csv','bytes':len(raw),
                   'git_blob_sha1':SOURCE_BLOB,'source_sha256':digest},
         'original_E5_qualified_count_unchanged':0,
         'source_animal_or_camera_ids_exported':False})
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=run(args.source)
    except (ValueError,OSError,RuntimeError) as exc:
        result={'schema_version':1,'status':'MC1_TERMINAL_SOURCE_OR_SCHEMA_STOP',
                'reason':str(exc)[:240],'biological_prediction_evaluated':False,
                'original_E5_qualified_count_unchanged':0}
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'support':result.get('support',{}),
                      'gain':result.get('primary',{}).get('heldout_brier_gain')},sort_keys=True))

if __name__=='__main__':
    main()
