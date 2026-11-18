#!/usr/bin/env python3
"""C3 one-shot Snapshot Europe 2021→2022 new-array country prior test.

FROZEN design committed BEFORE any animal record was accessed:
docs/replication/C3_CROSSYEAR_COUNTRY_PRIOR_FROZEN_DESIGN.md

This estimates recorded camera mammal incidence; never true presence, a
regional pool mechanism, detection calibration, or eSDM superiority.
No image rows or published camera-list rows are opened.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

FILE_ID = 345505
ZIP_BYTES = 77352666
ZIP_MD5 = '102a0e35504eaa95c1b59bcd71c42a0d'
ZIP_SHA256 = '8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54'
SOURCE_URL = f'https://edmond.mpg.de/api/access/datafile/{FILE_ID}'
PRE_RESPONSE_DESIGN = 'docs/replication/C3_CROSSYEAR_COUNTRY_PRIOR_FROZEN_DESIGN.md'
STEM = 'DataS1/Snapshot_Europe_2021_2022_'
FILES = {name: STEM + name + '.csv' for name in ('projects', 'deployments', 'sequences')}
REQUIRED = {
    'projects': {'year', 'project_id', 'country_code'},
    'deployments': {'year', 'project_id', 'deployment_id', 'longitude', 'latitude',
                    'start_date', 'end_date', 'camera_id', 'camera_functioning',
                    'subproject_name_no_year'},
    'sequences': {'year', 'project_id', 'deployment_id', 'sequence_id',
                  'is_blank', 'class', 'genus', 'species', 'start_time'},
}
SYNTHETIC_ONLY_OBSERVATION = False
MIN_DAYS = 20
WINDOW_START = (9, 1)
WINDOW_END = (10, 31)
MIN_TRAIN_CAMERAS = 200
MIN_HOLDOUT_CAMERAS = 200
MIN_SHARED_COUNTRIES = 5
MIN_PER_COUNTRY = 10
MIN_SPECIES = 8
MAX_SPECIES = 20
MIN_TAXON_CAMERAS = 10
MIN_TAXON_COUNTRIES = 3
SHRINK_CAMERAS = 20
BETA_GAIN_GATE = 0.002
POSITIVE_COUNTRY_FRACTION_GATE = 0.60
NEGATIVE_FUNCTION = {'false', 'no', '0', 'n', 'broken', 'not functioning'}
POSITIVE_BLANK = {'true', 'yes', '1', 'y'}
EXCLUDED_DOMESTIC = {
    'Homo sapiens', 'Felis catus', 'Canis familiaris', 'Bos taurus',
    'Equus caballus', 'Ovis aries', 'Capra hircus',
}
GENUS = re.compile(r'^[A-Z][a-z]+$')
EPITHET = re.compile(r'^[a-z][a-z-]+$')
ISO_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}(?!\d)')


def hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def source_guard(path: Path) -> dict:
    if path.stat().st_size != ZIP_BYTES or hash_file(path, 'md5') != ZIP_MD5 or hash_file(path, 'sha256') != ZIP_SHA256:
        raise ValueError('TRANSPORT_OR_SOURCE_STOP: frozen Edmond v2.0 source bytes differ')
    return {'doi': '10.17617/3.7YLWMU', 'version': '2.0', 'file_id': FILE_ID,
            'url': SOURCE_URL, 'zip_bytes': ZIP_BYTES, 'md5': ZIP_MD5,
            'sha256': ZIP_SHA256}


def parse_year(value: str):
    try:
        y = int(value.strip())
    except (ValueError, AttributeError):
        return None
    return y if y in (2021, 2022) else None


def parse_date(value: str):
    if not isinstance(value, str) or ISO_DATE.match(value.strip()) is None:
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def exposure_days(year: int, start: str, end: str):
    a, b = parse_date(start), parse_date(end)
    if a is None or b is None or b < a:
        return None
    left = max(a, date(year, *WINDOW_START))
    right = min(b, date(year, *WINDOW_END))
    return max(0, (right-left).days + 1)


def clean_species(genus: str, epithet: str):
    g, s = genus.strip(), epithet.strip()
    if not GENUS.fullmatch(g) or not EPITHET.fullmatch(s):
        return None
    name = f'{g} {s}'
    return name if name not in EXCLUDED_DOMESTIC else None


def guarded_rows(z: ZipFile, kind: str):
    filename = FILES[kind]
    if filename not in z.namelist():
        raise ValueError(f'RESPONSE_SCHEMA_STOP: missing {kind} archive member')
    with z.open(filename) as binary, io.TextIOWrapper(binary, encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not REQUIRED[kind].issubset(set(reader.fieldnames or [])):
            raise ValueError(f'RESPONSE_SCHEMA_STOP: {kind} CSV required header columns missing')
        yield from reader


def parse_projects(rows):
    projects, qc = {}, Counter()
    for row in rows:
        y = parse_year(row.get('year', ''))
        if y is None:
            qc['outside_2021_2022'] += 1
            continue
        key = (y, row['project_id'].strip())
        country = row['country_code'].strip()
        if not key[1] or not country:
            qc['invalid_project_country'] += 1
            continue
        if key in projects and projects[key] != country:
            raise ValueError('RESPONSE_SCHEMA_STOP: conflicting project-country identity')
        if key in projects:
            qc['exact_duplicate_project'] += 1
            continue
        projects[key] = country
    return projects, dict(qc)


def parse_deployments(rows, projects):
    # Effective unit: camera x year x project; repeated deployments collapse.
    cameras, eligible_deployments = {}, {}
    deployment_fields = {}
    qc = Counter()
    for row in rows:
        qc['total_deployment_rows'] += 1
        y = parse_year(row['year'])
        if y is None:
            qc['outside_2021_2022'] += 1
            continue
        p, d, camera = (row[k].strip() for k in ('project_id', 'deployment_id', 'camera_id'))
        dep = (y, p, d)
        immutable = tuple(row.get(k, '').strip() for k in sorted(REQUIRED['deployments']))
        if not p or not d:
            qc['invalid_identity'] += 1
            continue
        if dep in deployment_fields:
            if deployment_fields[dep] != immutable:
                raise ValueError('RESPONSE_SCHEMA_STOP: conflicting deployment identity')
            qc['exact_duplicate_deployment'] += 1
            continue
        deployment_fields[dep] = immutable
        country = projects.get((y, p))
        array = row['subproject_name_no_year'].strip()
        if not country or not array or not camera:
            qc['missing_country_array_or_camera'] += 1
            continue
        start, end = parse_date(row['start_date']), parse_date(row['end_date'])
        days = exposure_days(y, row['start_date'], row['end_date'])
        if days is None or days < MIN_DAYS:
            qc['inadequate_or_invalid_exposure'] += 1
            continue
        try:
            lon, lat = float(row['longitude']), float(row['latitude'])
        except (ValueError, TypeError):
            qc['bad_coordinates'] += 1
            continue
        if not(math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90):
            qc['bad_coordinates'] += 1
            continue
        functioning = row['camera_functioning'].strip().lower()
        if functioning in NEGATIVE_FUNCTION:
            qc['explicit_nonfunctioning'] += 1
            continue
        if functioning not in {'true', 'yes', '1', 'y'}:
            qc['unknown_functioning_retained'] += 1
        cid = (y, p, camera)
        arr = (country, array)
        if cid in cameras and cameras[cid]['array'] != arr:
            raise ValueError('RESPONSE_SCHEMA_STOP: physical camera mapped to conflicting country/array')
        cameras[cid] = {'year': y, 'country': country, 'array': arr}
        eligible_deployments[dep] = (cid, start, end)
        qc['eligible_deployment_rows'] += 1
    return cameras, eligible_deployments, dict(qc)


def parse_sequences(rows, eligible_deployments):
    detections = defaultdict(set)
    qc=Counter()
    seen_sequences={}
    seen_record=set()
    for row in rows:
        qc['total_sequence_rows'] += 1
        y=parse_year(row.get('year',''))
        if y is None:
            qc['outside_2021_2022'] += 1
            continue
        p,d,sid = (row[k].strip() for k in ('project_id','deployment_id','sequence_id'))
        if not p or not d or not sid:
            qc['invalid_identity'] += 1
            continue
        sk=(y,p,sid)
        dep=(y,p,d)
        if sk in seen_sequences and seen_sequences[sk]!=dep:
            raise ValueError('RESPONSE_SCHEMA_STOP: sequence ID maps to multiple deployments')
        seen_sequences[sk]=dep
        if dep not in eligible_deployments:
            qc['ineligible_or_unknown_deployment'] += 1
            continue
        if row['is_blank'].strip().lower() in POSITIVE_BLANK:
            qc['blank_sequence'] += 1
            continue
        if row['class'].strip().lower()!='mammalia':
            qc['non_mammal'] += 1
            continue
        species=clean_species(row['genus'],row['species'])
        if not species:
            qc['non_binomial_or_excluded_domestic'] += 1
            continue
        stamp=parse_date(row['start_time'])
        if stamp is None or stamp.year!=y or not date(y,*WINDOW_START)<=stamp<=date(y,*WINDOW_END):
            qc['invalid_or_outside_window_timestamp'] += 1
            continue
        cid,start,end=eligible_deployments[dep]
        if not start<=stamp<=end:
            qc['timestamp_outside_deployment'] += 1
            continue
        triple=(cid,sid,species)
        if triple in seen_record:
            qc['duplicate_camera_sequence_species'] += 1
            continue
        seen_record.add(triple)
        detections[cid].add(species)
        qc['eligible_recorded_mammal_sequences'] += 1
    return detections, dict(qc)


def one_year_subsets(cameras, detections):
    train = {c:row for c,row in cameras.items() if row['year']==2021}
    training_arrays={row['array'] for row in train.values()}
    val={c:row for c,row in cameras.items() if row['year']==2022 and row['array'] not in training_arrays}
    exclusion=Counter(row['array'] in training_arrays for c,row in cameras.items() if row['year']==2022)
    return train, val, {'2022_cameras_in_shared_2021_arrays_excluded':exclusion[True],
                        '2022_cameras_new_array_retained':exclusion[False]}


def choose_roster(train, detections):
    camera_hits=Counter()
    country_hits=defaultdict(set)
    for c,row in train.items():
        for sp in detections.get(c,()):
            camera_hits[sp]+=1
            country_hits[sp].add(row['country'])
    return tuple(sp for sp,n in sorted(camera_hits.items(),key=lambda z:(-z[1],z[0]))
                 if n>=MIN_TAXON_CAMERAS and len(country_hits[sp])>=MIN_TAXON_COUNTRIES)[:MAX_SPECIES]


def brier_fit_score(train,val,detections,roster):
    ntrain=len(train)
    per_train=Counter(row['country'] for row in train.values())
    per_hold=Counter(row['country'] for row in val.values())
    species_counts=Counter(sp for cid in train for sp in detections.get(cid,()) if sp in roster)
    country_sp=Counter((train[cid]['country'],sp) for cid in train for sp in detections.get(cid,()) if sp in roster)
    globals={sp:(species_counts[sp]+1)/(ntrain+2) for sp in roster}
    predfull={}
    for country in per_hold:
        for sp in roster:
            g=globals[sp]
            predfull[country,sp]=(country_sp[country,sp]+SHRINK_CAMERAS*g)/(per_train[country]+SHRINK_CAMERAS) if per_train[country]>=MIN_PER_COUNTRY else g
    lossbase=lossfull=0.0
    per_country=defaultdict(lambda:[0.0,0.0,0])
    for cid,row in val.items():
        country=row['country']
        positives=detections.get(cid,set())
        for sp in roster:
            true=float(sp in positives)
            g=globals[sp];p=predfull[country,sp]
            ebase=(true-g)**2;efull=(true-p)**2
            lossbase+=ebase;lossfull+=efull
            d=per_country[country]
            d[0]+=ebase;d[1]+=efull;d[2]+=1
    n=len(val)*len(roster)
    if not n:
        raise ValueError('INSUFFICIENT_TRANSFER_SUPPORT: no camera × taxon observations')
    baseline=lossbase/n
    full=lossfull/n
    shares=sorted(c for c in per_country if per_train[c]>=MIN_PER_COUNTRY and per_hold[c]>=MIN_PER_COUNTRY)
    country_gains={c:(per_country[c][0]-per_country[c][1])/per_country[c][2] for c in shares}
    pos=sum(z>0 for z in country_gains.values())
    frac=pos/len(shares) if shares else None
    return {'brier_global':baseline,'brier_country_prior':full,
            'primary_gain':baseline-full,
            'qualifying_shared_countries':len(shares),
            'qualifying_countries_positive':pos,
            'positive_country_fraction':frac,
            'target_camera_taxon_cells':n,
            'positive_rule_passed': baseline-full>=BETA_GAIN_GATE and frac is not None and frac>=POSITIVE_COUNTRY_FRACTION_GATE}


def evaluate(cameras, detections, source=None, metadata_qc=None, sequence_qc=None):
    train,val,split_qc=one_year_subsets(cameras,detections)
    roster=choose_roster(train,detections)
    train_countries=Counter(x['country'] for x in train.values())
    val_countries=Counter(x['country'] for x in val.values())
    shared={c for c in train_countries if train_countries[c]>=10 and val_countries[c]>=10}
    summary={'schema_version':1,'status':'INSUFFICIENT_TRANSFER_SUPPORT',
             'date':'2026-11-18','source':source or {},'frozen_design':PRE_RESPONSE_DESIGN,
             'observation_grain':'camera-by-frozen-mammal-label recorded incidence',
             'support':{'training_cameras':len(train),'new_array_validation_cameras':len(val),
                        'training_arrays':len({x['array'] for x in train.values()}),
                        'validation_new_arrays':len({x['array'] for x in val.values()}),
                        'training_countries':len(train_countries),'validation_countries':len(val_countries),
                        'qualifying_shared_countries':len(shared),'roster_species_count':len(roster)},
             'metadata_quality':metadata_qc or {},'sequence_quality':sequence_qc or {},
             'array_holdout_quality':split_qc,
             'limits':{'not_detection_calibrated':True,'not_occupancy_estimate':True,
                       'country_not_verified_biogeographic_source_pool':True,
                       'not_eSDM_fit_or_superiority_evidence':True,
                       'prior_E4_E5_E7_Safari14_C1_C2_unchanged':True}}
    if len(train)<MIN_TRAIN_CAMERAS or len(val)<MIN_HOLDOUT_CAMERAS or len(shared)<MIN_SHARED_COUNTRIES or len(roster)<MIN_SPECIES:
        summary['stop_reason']='frozen physical-camera/country/species minimum not met'
        return summary
    scores=brier_fit_score(train,val,detections,roster)
    summary['primary']=scores
    summary['nonfocal_holdout_mammal_label_count']=len({sp for cid in val for sp in detections.get(cid,set()) if sp not in roster})
    summary['status']='POSITIVE_DESCRIPTIVE_COUNTRY_PRIOR_TRANSFER' if scores['positive_rule_passed'] else 'NO_USEFUL_COUNTRY_PRIOR_TRANSFER'
    return summary


def run(path:Path, stage=None):
    source=source_guard(path)
    with ZipFile(path) as archive:
        projects,pqc=parse_projects(guarded_rows(archive,'projects'))
        cams,deployments,dqc=parse_deployments(guarded_rows(archive,'deployments'),projects)
        if stage is not None:
            stage['animal_response_opening_started'] = True
        hits,sqc=parse_sequences(guarded_rows(archive,'sequences'),deployments)
    return evaluate(cams,hits,source,{'projects':pqc,'deployments':dqc},sqc)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--zip',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    stage={'animal_response_opening_started':False}
    unexpected=False
    try:
        result=run(args.zip,stage=stage)
    except (ValueError, BadZipFile, KeyError, UnicodeError, csv.Error) as exc:
        msg=str(exc)
        status=next((tag for tag in ('TRANSPORT_OR_SOURCE_STOP','RESPONSE_SCHEMA_STOP')
                     if msg.startswith(tag)), 'UNEXPECTED_PROGRAM_STOP')
        unexpected=(status=='UNEXPECTED_PROGRAM_STOP')
        # No raw biological values, species or camera identifiers in terminal artifact.
        result={'schema_version':1,'date':'2026-11-18','status':status,
                'frozen_design':PRE_RESPONSE_DESIGN,'source':{'doi':'10.17617/3.7YLWMU',
                    'file_id':FILE_ID,'published_md5':ZIP_MD5,'published_sha256':ZIP_SHA256},
                'stop_reason':msg if not unexpected else 'unexpected parse/program error',
                'source_animal_response_may_have_been_opened':stage['animal_response_opening_started'],
                'ecological_transfer_test_completed':False,
                'prior_ecological_results_unchanged':True}
    result['execution']={'workflow_sha':os.environ.get('GITHUB_SHA'), 'run_id':os.environ.get('GITHUB_RUN_ID')}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'support':result.get('support'),
        'primary_gain':result.get('primary',{}).get('primary_gain')},sort_keys=True))
    if unexpected:
        raise SystemExit(2)

if __name__=='__main__':
    main()
