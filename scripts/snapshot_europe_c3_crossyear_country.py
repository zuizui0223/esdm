#!/usr/bin/env python3
"""One-shot C3, pre-response-frozen 2021→2022 camera-incidence prior transfer.

No image file or animal event data are exported. Source must match published
Edmond DataS1 version 2.0 MD5 and response-blind SHA256. The outcome is
*recorded mammal species at a camera*, not true occupancy or a G4 calibration.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

SOURCE_DOI = '10.17617/3.7YLWMU'
SOURCE_FILE_ID = 345505
SOURCE_SIZE = 77352666
SOURCE_MD5 = '102a0e35504eaa95c1b59bcd71c42a0d'
SOURCE_SHA256 = '8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54'
PREFIX = 'DataS1/Snapshot_Europe_2021_2022_'
MEMBERS = {name: PREFIX + name + '.csv' for name in ('deployments', 'projects', 'sequences')}
REQUIRED = {
    'deployments': ('year','project_id','deployment_id','longitude','latitude','start_date','end_date','camera_id','camera_functioning','subproject_name_no_year'),
    'projects': ('year','project_id','country_code'),
    'sequences': ('year','project_id','deployment_id','sequence_id','is_blank','class','genus','species','start_time'),
}
DOMESTIC = frozenset({'Homo sapiens','Felis catus','Canis familiaris','Bos taurus','Equus caballus','Ovis aries','Capra hircus'})
NOT_FUNCTIONING = frozenset({'false','no','0','n','broken','not functioning'})
IS_BLANK = frozenset({'true','yes','1','y'})
BINOMIAL = re.compile(r'^[A-Za-z]+$')
DATE_PREFIX = re.compile(r'^\d{4}-\d{2}-\d{2}')
MIN_OVERLAP_DAYS = 20
MIN_COUNTRY_TRAIN = 10
COUNTRY_SHRINKAGE_CAMERAS = 20
MAX_TAXA = 20
MIN_ROSTER_SPECIES = 8
MIN_TRAIN_CAMERAS = 200
MIN_HELDOUT_CAMERAS = 200
MIN_ESTIMABLE_COUNTRIES = 5
COUNTRY_FRACTION_THRESHOLD = 0.60
BRIER_GAIN_THRESHOLD = 0.002


def _digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_source(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size != SOURCE_SIZE:
        raise ValueError('SOURCE_STOP: source byte size not the pinned Edmond v2 file')
    md5, sha = _digest(path,'md5'), _digest(path,'sha256')
    if (md5,sha) != (SOURCE_MD5,SOURCE_SHA256):
        raise ValueError('SOURCE_STOP: published MD5 or response-blind SHA256 mismatch')
    return {'doi': SOURCE_DOI,'edmond_datafile_id':SOURCE_FILE_ID,'zip_bytes':SOURCE_SIZE,
            'md5':md5,'sha256':sha,'source_version':'2.0',
            'raw_image_file_opened':False}


def _iter_dicts(archive: ZipFile, name: str):
    try:
        stream = archive.open(MEMBERS[name])
    except KeyError as exc:
        raise ValueError('RESPONSE_SCHEMA_STOP: required source member absent') from exc
    with stream, io.TextIOWrapper(stream,encoding='utf-8-sig',newline='') as handle:
        reader = csv.DictReader(handle)
        if not set(REQUIRED[name]).issubset(reader.fieldnames or []):
            raise ValueError('RESPONSE_SCHEMA_STOP: required columns absent')
        if reader.fieldnames and len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('RESPONSE_SCHEMA_STOP: duplicate header columns')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('RESPONSE_SCHEMA_STOP: malformed tabular row')
            yield row


def _year(value: str) -> int | None:
    value = value.strip()
    return int(value) if value in ('2021','2022') else None


def _calendar(value: str) -> date | None:
    v = value.strip()
    if not DATE_PREFIX.match(v):
        return None
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        return None


def _window(year: int):
    return date(year,9,1),date(year,10,31)


def _safe_float(value: str) -> float | None:
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def parse_projects(archive: ZipFile):
    projects = {}
    original_rows = {}
    qc = Counter()
    for row in _iter_dicts(archive,'projects'):
        qc['rows'] += 1
        year = _year(row['year'])
        if year is None:
            qc['other_year'] += 1; continue
        project_id = row['project_id'].strip()
        if not project_id:
            qc['blank_project_id'] += 1; continue
        key = (year,project_id)
        canonical = tuple(sorted(row.items()))
        if key in original_rows:
            if original_rows[key] != canonical:
                raise ValueError('RESPONSE_SCHEMA_STOP: conflicting project metadata keys')
            qc['duplicate_exact_projects'] += 1
            continue
        original_rows[key] = canonical
        country = row['country_code'].strip()
        if not country:
            qc['missing_country'] += 1; continue
        projects[key] = country
    return projects, dict(qc)


def parse_deployments(archive: ZipFile, projects: dict):
    deployments, physical = {}, {}
    rows_seen = {}
    qc = Counter()
    for row in _iter_dicts(archive,'deployments'):
        qc['rows'] += 1
        year = _year(row['year'])
        if year is None:
            qc['other_year'] += 1; continue
        project, deployment = row['project_id'].strip(), row['deployment_id'].strip()
        if not project or not deployment:
            qc['missing_project_deployment_id'] += 1; continue
        key = (year,project,deployment)
        canonical = tuple(sorted(row.items()))
        if key in rows_seen:
            if rows_seen[key] != canonical:
                raise ValueError('RESPONSE_SCHEMA_STOP: conflicting deployment metadata keys')
            qc['duplicate_exact_deployments'] += 1
            continue
        rows_seen[key] = canonical
        country = projects.get((year,project))
        if country is None:
            qc['missing_country_project_join'] += 1; continue
        camera = row['camera_id'].strip()
        array = row['subproject_name_no_year'].strip()
        if not camera or not array:
            qc['missing_camera_or_array'] += 1; continue
        raw_flag=row['camera_functioning'].strip().casefold()
        if raw_flag in NOT_FUNCTIONING:
            qc['explicit_nonfunctioning'] += 1; continue
        start, end = _calendar(row['start_date']), _calendar(row['end_date'])
        if start is None or end is None or end < start:
            qc['invalid_date_interval'] += 1; continue
        ws,we = _window(year)
        overlap_start, overlap_end = max(ws,start), min(we,end)
        if overlap_end < overlap_start or (overlap_end-overlap_start).days+1 < MIN_OVERLAP_DAYS:
            qc['insufficient_window_overlap_days'] += 1; continue
        lon,lat=_safe_float(row['longitude']),_safe_float(row['latitude'])
        if lon is None or lat is None or not (-180<=lon<=180 and -90<=lat<=90):
            qc['invalid_geo'] += 1; continue
        if not raw_flag:
            qc['eligible_deployments_unknown_functioning'] += 1
        camera_key = (year, project, camera)
        array_key = (country,array)
        if camera_key in physical and physical[camera_key] != array_key:
            raise ValueError('RESPONSE_SCHEMA_STOP: physical camera maps to multiple country/array values')
        physical[camera_key] = array_key
        deployments[key]={'camera':camera_key,'array':array_key,
                          'start':overlap_start,'end':overlap_end}
        qc['eligible_deployments'] += 1
    qc['eligible_physical_cameras'] = len(physical)
    qc['eligible_arrays'] = len(set(physical.values()))
    return deployments,physical,dict(qc)


def _taxon(row:dict) -> str | None:
    genus=row['genus'].strip()
    species=row['species'].strip()
    if not BINOMIAL.fullmatch(genus) or not BINOMIAL.fullmatch(species):
        return None
    return genus[0].upper()+genus[1:].lower()+' '+species.lower()


def parse_sequences(archive:ZipFile,deployments:dict):
    obs=defaultdict(set)
    owner={}
    dedupe=set()
    qc=Counter()
    for row in _iter_dicts(archive,'sequences'):
        qc['rows']+=1
        year=_year(row['year'])
        if year is None:
            qc['other_year']+=1;continue
        project,dep,seq=(row[k].strip() for k in ('project_id','deployment_id','sequence_id'))
        if not project or not dep or not seq:
            qc['blank_sequence_or_join_key']+=1; continue
        sequence_key=(year,project,seq)
        if sequence_key in owner and owner[sequence_key]!=dep:
            raise ValueError('RESPONSE_SCHEMA_STOP: sequence identity maps to conflicting deployments')
        owner[sequence_key]=dep
        detail=deployments.get((year,project,dep))
        if detail is None:
            qc['ineligible_deployment']+=1;continue
        if row['is_blank'].strip().casefold() in IS_BLANK:
            qc['marked_blank']+=1;continue
        if row['class'].strip().casefold()!='mammalia':
            qc['nonmammal']+=1;continue
        taxon=_taxon(row)
        if taxon is None:
            qc['not_valid_species_binomial']+=1;continue
        if taxon in DOMESTIC:
            qc['excluded_domestic_or_human']+=1;continue
        seen_time=_calendar(row['start_time'])
        if seen_time is None or seen_time < detail['start'] or seen_time > detail['end']:
            qc['time_outside_verified_deployment_window']+=1;continue
        unique=(sequence_key,taxon,detail['camera'])
        if unique in dedupe:
            qc['duplicate_sequence_species_camera']+=1;continue
        dedupe.add(unique)
        obs[detail['camera']].add(taxon)
        qc['eligible_sequence_taxon_records']+=1
    qc['positive_physical_cameras']=len(obs)
    return obs,dict(qc)


def select_roster(training:list[tuple], obs:dict, physical:dict)->list[str]:
    counts=Counter()
    countries=defaultdict(set)
    for cam in training:
        country=physical[cam][0]
        for taxon in obs.get(cam,set()):
            counts[taxon]+=1
            countries[taxon].add(country)
    return [taxon for taxon in sorted(counts,key=lambda s:(-counts[s],s))
            if counts[taxon]>=10 and len(countries[taxon])>=3][:MAX_TAXA]


def grouped_cameras(physical:dict):
    seen_train={key for cam,key in physical.items() if cam[0]==2021}
    training=sorted([cam for cam in physical if cam[0]==2021])
    heldout=sorted([cam for cam,key in physical.items()
                    if cam[0]==2022 and key not in seen_train])
    removed=sum(1 for cam,key in physical.items() if cam[0]==2022 and key in seen_train)
    return training,heldout,seen_train,removed


def _brier(count:float,squared:float):
    return squared/count if count else None


def evaluate(physical:dict, obs:dict)->dict:
    train,validation,train_arrays,removed=grouped_cameras(physical)
    roster=select_roster(train,obs,physical)
    train_countries=Counter(physical[cam][0] for cam in train)
    hold_countries=Counter(physical[cam][0] for cam in validation)
    qualifying=sorted(c for c,n in hold_countries.items()
                      if n>=10 and train_countries.get(c,0)>=10)
    base_support={
        'training_cameras':len(train),'training_arrays':len(train_arrays),
        'training_countries':len(train_countries),
        'heldout_new_array_cameras':len(validation),
        'heldout_new_arrays':len({physical[c] for c in validation}),
        'heldout_new_array_countries':len(hold_countries),
        'excluded_shared_array_2022_cameras':removed,
        'roster_species_count':len(roster),
        'estimable_shared_countries':len(qualifying),
    }
    if (len(train)<MIN_TRAIN_CAMERAS or len(validation)<MIN_HELDOUT_CAMERAS
            or len(roster)<MIN_ROSTER_SPECIES or len(qualifying)<MIN_ESTIMABLE_COUNTRIES):
        return {'status':'INSUFFICIENT_TRANSFER_SUPPORT','support':base_support,
                'reason':'predeclared 2021 camera, 2022 novel array, country or 2021 roster support not reached'}
    positive_global=Counter(s for cam in train for s in (obs.get(cam,set()) & set(roster)))
    positive_country=defaultdict(Counter)
    for cam in train:
        country=physical[cam][0]
        for species in obs.get(cam,set()) & set(roster):
            positive_country[country][species]+=1
    ntrain=len(train)
    global_prior={s:(positive_global[s]+1)/(ntrain+2) for s in roster}
    country_prior={}
    for country in hold_countries:
        n=train_countries.get(country,0)
        country_prior[country]={s:(positive_country[country][s]+COUNTRY_SHRINKAGE_CAMERAS*global_prior[s])/(n+COUNTRY_SHRINKAGE_CAMERAS)
            if n>=MIN_COUNTRY_TRAIN else global_prior[s] for s in roster}
    err_global=err_country=0.0
    country_sums=defaultdict(lambda:[0,0.,0.])
    for cam in validation:
        country=physical[cam][0]
        detected=obs.get(cam,set())
        for species in roster:
            y=1.0 if species in detected else 0.0
            g=global_prior[species]
            c=country_prior[country][species]
            delta_g=(y-g)**2
            delta_c=(y-c)**2
            err_global+=delta_g
            err_country+=delta_c
            v=country_sums[country]
            v[0]+=1;v[1]+=delta_g;v[2]+=delta_c
    nrows=len(validation)*len(roster)
    brier_g=err_global/nrows
    brier_gc=err_country/nrows
    country_rows=[]
    for country in sorted(country_sums):
        n,g,c=country_sums[country]
        country_rows.append({'country_code':country,
             'train_cameras':train_countries.get(country,0),
             'heldout_cameras':hold_countries[country],
             'target_camera_species_rows':n,
             'brier_G':g/n,'brier_G_plus_country':c/n,
             'brier_gain':(g-c)/n,
             'estimable_shared_country':country in qualifying})
    npos=sum(x['brier_gain']>0 for x in country_rows if x['estimable_shared_country'])
    positive_fraction=npos/len(qualifying)
    gain=brier_g-brier_gc
    supported=(gain>=BRIER_GAIN_THRESHOLD and positive_fraction>=COUNTRY_FRACTION_THRESHOLD)
    newly_recorded_2022={s for cam in validation for s in obs.get(cam,set())}
    return {'status':('POSITIVE_DESCRIPTIVE_COUNTRY_PRIOR_TRANSFER' if supported else 'NO_USEFUL_COUNTRY_PRIOR_TRANSFER'),
          'support':base_support,
          'primary':{'Brier_G':brier_g,'Brier_G_plus_country':brier_gc,
                     'Brier_gain_G_minus_G_plus_country':gain,
                     'positive_country_count':npos,
                     'positive_country_fraction':positive_fraction,
                     'minimum_Brier_gain':BRIER_GAIN_THRESHOLD,
                     'minimum_positive_country_fraction':COUNTRY_FRACTION_THRESHOLD,
                     'predeclared_positive_rule_met':supported,
                     'target_camera_species_rows':nrows,
                     'country_smoothing_pseudo_cameras':COUNTRY_SHRINKAGE_CAMERAS,
                     'global_beta_prior':'one_positive_one_negative',
                     'country_min_training_cameras':MIN_COUNTRY_TRAIN},
          'countries':country_rows,
          'novel_2022_nonfocal_taxa_count':len(newly_recorded_2022-set(roster)),
          'summary_only':True}


def analyze_archive(path: Path) -> dict:
    source=verify_source(path)     # do not open ZIP members before integrity check
    try:
        with ZipFile(path) as z:
            projects,qprojects=parse_projects(z)
            deployments,physical,qdeploy=parse_deployments(z,projects)
            obs,qsequences=parse_sequences(z,deployments)
    except BadZipFile as exc:
        raise ValueError('SOURCE_STOP: published ZIP archive invalid') from exc
    result=evaluate(physical,obs)
    result.update({'schema_version':1,'date':'2026-11-18',
         'source':source,
         'quality':{'projects':qprojects,'deployments':qdeploy,'sequences':qsequences},
         'frozen_design':'docs/replication/C3_CROSSYEAR_COUNTRY_PRIOR_FROZEN_DESIGN.md',
         'original_prior_results_unchanged':True,
         'limits':{'camera_record_not_true_occupancy':True,'country_is_proxy_not_accessible_species_pool':True,
                   'observation_detection_not_calibrated':True,'e5_g4_not_qualified':True,
                   'not_process_based_esdm_field_fit':True,
                   'not_causal_IBD_IBE_or_dispersal':True,'no_p_value_or_CI':True}})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    # Initial sentinel is written even when executed directly. The workflow also
    # writes its own transport sentinel *before* downloading any biological bytes.
    result={'schema_version':1,'status':'SOURCE_STOP','date':'2026-11-18',
            'biology_result_computed':False,'reason':'Source validation did not complete'}
    try:
        result=analyze_archive(args.zip)
    except ValueError as exc:
        message=str(exc)
        status=message.split(':',1)[0]
        if status not in ('SOURCE_STOP','RESPONSE_SCHEMA_STOP'):
            status='RESPONSE_SCHEMA_STOP'
        result={'schema_version':1,'date':'2026-11-18','status':status,
                'biology_result_computed':False,
                'reason':message[:180],
                'original_prior_results_unchanged':True}
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],
                      'support':result.get('support',{}),
                      'primary':result.get('primary',{}).get('Brier_gain_G_minus_G_plus_country'),
                      'biology_result_computed':result.get('biology_result_computed',result['status'] not in ('SOURCE_STOP','RESPONSE_SCHEMA_STOP','INSUFFICIENT_TRANSFER_SUPPORT'))},sort_keys=True))

if __name__=='__main__':
    main()
