#!/usr/bin/env python3
"""NEON C2: one-shot, SHA-locked, region-restricted camera-incidence null.

The frozen design is docs/replication/NEON_C2_REGION_CONSTRAINED_FROZEN_DESIGN.md,
committed BEFORE inspecting the Zenodo species response. Observational recorded
species labels only; neither a calibrated detection model nor eSDM fit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
from statistics import median

DOI = '10.5281/zenodo.20826511'
EXPECTED_MD5 = {
    'deployment': '82537cdf0a586fa14c9a8b6afd7be470',
    'sequence': '7531a5b9fb3848ef33e162d5206a6f43',
    'description': 'be1502427995886ef1c64c10410d1ee2',
}
DEP_REQUIRED = {'deployment_id','placename','longitude','latitude','start_date','end_date','subproject_name'}
SEQ_REQUIRED = {'deployment_id','sequence_id','class','genus','species'}
MIN_DAYS = 20
MIN_CAMERAS = 20
CAMERAS_PER_DRAW = 10
SPECIES_PER_PROJECT_MIN_CAMERAS = 2
DRAWS = 200
BURN_PER_ROW = 30
BETWEEN_PER_ROW = 15
REGIONS = ('East','West')
SEEDS = {'East': 20261118, 'West': 20261117}
DOMESTIC = {'Homo sapiens','Felis catus','Canis familiaris',
            'Canis lupus familiaris','Bos taurus','Equus caballus',
            'Ovis aries','Capra hircus'}


def digest(path: Path, algorithm: str) -> str:
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def verify_sources(paths):
    actual={k:digest(p,'md5') for k,p in paths.items()}
    if actual!=EXPECTED_MD5:
        raise ValueError('TRANSPORT_OR_SOURCE_STOP: Zenodo MD5 drift '+str({k:actual[k] for k in actual if actual[k]!=EXPECTED_MD5[k]}))
    return {'doi':DOI,'md5':actual,'sha256':{k:digest(p,'sha256') for k,p in paths.items()},
            'source_version':'v1'}


def _valid_coords(lon,lat):
    return math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90<=lat<=90


def read_deployments(path:Path):
    by_id={}
    qual=Counter()
    with path.open(encoding='utf-8-sig', newline='') as f:
        r=csv.DictReader(f)
        if not DEP_REQUIRED.issubset(set(r.fieldnames or [])):
            raise ValueError('DEPLOYMENT_SCHEMA_STOP: missing required columns')
        for row in r:
            qual['total_deployment_rows']+=1
            key=row['deployment_id'].strip()
            if not key:
                qual['blank_id']+=1
                continue
            # Duplicate deployment IDs must not refer to different source cameras.
            identity=(row['subproject_name'].strip(), row['placename'].strip())
            if not all(identity):
                qual['blank_site_or_project']+=1
                continue
            try:
                lon,lat=float(row['longitude']),float(row['latitude'])
                start,end=date.fromisoformat(row['start_date']),date.fromisoformat(row['end_date'])
            except (ValueError,TypeError):
                qual['invalid_date_or_coordinate']+=1
                continue
            if not _valid_coords(lon,lat) or (end-start).days<MIN_DAYS:
                qual['invalid_location_or_short_interval']+=1
                continue
            data={'identity':identity,'lon':lon,'lat':lat,'start':start.isoformat(),
                  'end':end.isoformat()}
            if key in by_id:
                if by_id[key]['identity']!=identity:
                    raise ValueError('DEPLOYMENT_SCHEMA_STOP: same ID maps to different physical cameras')
                # Repeated identical deployment metadata is a no-op. Non-identical intervals
                # with the same deployment ID are ambiguous, so fail closed.
                if by_id[key]!=data:
                    raise ValueError('DEPLOYMENT_SCHEMA_STOP: conflicting duplicate deployment ID')
                qual['identical_duplicate_ids']+=1
                continue
            by_id[key]=data
            qual['qualified_deployment_ids']+=1
    cameras=defaultdict(lambda:{'ids':set(),'coords':[],'species':set()})
    for did,dat in by_id.items():
        cam=cameras[dat['identity']]
        cam['ids'].add(did)
        cam['place']=dat['identity'][1]
        cam['coords'].append((dat['lon'],dat['lat']))
    return by_id,cameras,dict(qual)


def read_sequence_labels(path: Path, by_id:dict, cameras:dict):
    q=Counter()
    taxonomy={}
    unique=set()
    with path.open(encoding='utf-8-sig', newline='') as f:
        rdr=csv.DictReader(f)
        if not SEQ_REQUIRED.issubset(set(rdr.fieldnames or [])):
            raise ValueError('RESPONSE_SCHEMA_STOP: sequence required field absent')
        for row in rdr:
            q['total_sequence_rows']+=1
            dep=row['deployment_id'].strip()
            if dep not in by_id:
                q['excluded_not_qualified_deployment']+=1
                continue
            cls=row['class'].strip().lower()
            genus=row['genus'].strip()
            epithet=row['species'].strip()
            if not genus or not epithet or not genus[0].isupper() or ' ' in genus or ' ' in epithet or not epithet.isalpha() or epithet.lower() in {'sp','spp','unknown','undetermined','unidentified'}:
                q['excluded_missing_or_invalid_binomial']+=1
                continue
            binomial=f'{genus} {epithet.lower()}'
            # All species-labelled mammal vs nonmammal taxonomic conflicts terminate.
            if binomial in taxonomy and taxonomy[binomial]!=cls:
                raise ValueError('RESPONSE_SCHEMA_STOP: taxonomic class conflicts for a binomial')
            taxonomy[binomial]=cls
            if cls!='mammalia':
                q['excluded_nonmammal']+=1
                continue
            if binomial in DOMESTIC:
                q['excluded_domestic']+=1
                continue
            seq=row['sequence_id'].strip()
            if not seq:
                q['excluded_blank_sequence_id']+=1
                continue
            tup=(dep,seq,binomial)
            if tup in unique:
                q['duplicate_deployment_sequence_taxon']+=1
                continue
            unique.add(tup)
            cameras[by_id[dep]['identity']]['species'].add(binomial)
            q['accepted_mammal_sequences']+=1
    # No species/timestamps/IDs exported, only count statistics.
    q['eligible_wild_mammal_taxa']=len({sp for x in cameras.values() for sp in x['species']})
    return dict(q)


def prepare_regions(cameras):
    by_project=defaultdict(list)
    for (project,place), cam in cameras.items():
        cam['lon']=median(z[0] for z in cam['coords'])
        cam['lat']=median(z[1] for z in cam['coords'])
        by_project[project].append(cam)
    supported={p:sorted(cams,key=lambda c:c['place'])
               for p,cams in by_project.items() if len(cams)>=MIN_CAMERAS}
    regions={r:{} for r in REGIONS}
    for project,cams in supported.items():
        xs=[c['lon'] for c in cams]
        region='West' if median(xs)<-100 else 'East'
        if any(('West' if x<-100 else 'East')!=region for x in xs):
            raise ValueError('DEPLOYMENT_SCHEMA_STOP: one project crosses fixed -100 meridian')
        regions[region][project]=cams
    qc={
        'all_unique_eligible_camera_sites':len(cameras),
        'source_subproject_labels':len(by_project),
        'ineligible_subprojects_less_than_20_cameras':len(by_project)-len(supported),
        'eligible_projects_by_region':{k:len(v) for k,v in regions.items()},
        'eligible_cameras_by_region':{k:sum(len(x) for x in v.values()) for k,v in regions.items()},
    }
    return regions,qc


def beta(x,y):
    a,b,c=len(x&y),len(x-y),len(y-x)
    den=a+min(b,c)
    if den==0:return None
    sim=min(b,c)/den
    sor=(b+c)/(2*a+b+c)
    return (sim,sor-sim)


def sampled_species(rows,selected):
    count=Counter(sp for i in selected for sp in rows[i])
    return {sp for sp,n in count.items() if n>=SPECIES_PER_PROJECT_MIN_CAMERAS}


def table_summary(region_projects,project_samples):
    allpairs={}
    for a,b in combinations(sorted(region_projects),2):
        allpairs[(a,b)]=beta(project_samples[a],project_samples[b])
    eligible=[x for x in allpairs.values() if x is not None]
    return {'pairs':allpairs,'pair_count':len(eligible),
            'median_sim':median(x[0] for x in eligible) if eligible else None,
            'median_sne':median(x[1] for x in eligible) if eligible else None}


def samples(projects,*,seed=20261117,n=DRAWS):
    rng=random.Random(seed)
    # Freeze camera ordering by lexicographically sorted project names and original
    # camera place names. Source camera labels are never exported in JSON.
    return [{p:rng.sample(range(len(projects[p])),CAMERAS_PER_DRAW)
             for p in sorted(projects)} for _ in range(n)]


def margin(rows):
    return (tuple(len(s) for s in rows),Counter(x for s in rows for x in s))


def trade(rows,rng):
    if len(rows)<2:return False
    a=rng.randrange(len(rows))
    b=rng.randrange(len(rows)-1)
    if b>=a:b+=1
    common=rows[a]&rows[b]
    ua=rows[a]-common
    ub=rows[b]-common
    if not ua or not ub:return False
    pool=sorted(ua|ub)
    rng.shuffle(pool)
    rows[a]=common|set(pool[:len(ua)])
    rows[b]=common|set(pool[len(ua):])
    return True


def quantiles(values):
    s=sorted(values)
    return [s[math.floor(0.05*(len(s)-1))],s[math.ceil(0.95*(len(s)-1))]] if s else None


def per_region(name, projects, *,draws=DRAWS, burn=BURN_PER_ROW, between=BETWEEN_PER_ROW):
    if len(projects)<3:
        return {'status':'INSUFFICIENT_REGION_SUPPORT','project_count':len(projects)}
    names=tuple(sorted(projects))
    rows=[]
    ranges={}
    for p in names:
        beg=len(rows)
        rows.extend(set(c['species']) for c in projects[p])
        ranges[p]=tuple(range(beg,len(rows)))
    marg=margin(rows)
    qselect=samples(projects,n=draws)
    rng=random.Random(SEEDS[name])
    real=[]
    for selected in qselect:
        tax={p:sampled_species([c['species'] for c in projects[p]],selected[p]) for p in names}
        real.append(table_summary(names,tax))
    # Reinitialize a separate null state; original rows above are left unchanged.
    nulls=[set(s) for s in rows]
    burned=sum(trade(nulls,rng) for _ in range(len(rows)*burn))
    if margin(nulls)!=marg:raise ValueError('FIXED_MARGIN_DRIFT after burn')
    accepted=0
    results=[]
    bypair=defaultdict(lambda:{'observed':[],'null':[]})
    pairs_expected=len(names)*(len(names)-1)//2
    for j,selected in enumerate(qselect):
        accepted+=sum(trade(nulls,rng) for _ in range(len(rows)*between))
        if j%50==0 and margin(nulls)!=marg:
            raise ValueError('FIXED_MARGIN_DRIFT within chain')
        poolsets={p:sampled_species(nulls,[ranges[p][i] for i in selected[p]]) for p in names}
        d=table_summary(names,poolsets)
        old=real[j]
        for k,val in old['pairs'].items():
            if val is not None: bypair[k]['observed'].append(val[0])
        for k,val in d['pairs'].items():
            if val is not None: bypair[k]['null'].append(val[0])
        complete=old['pair_count']>=3 and d['pair_count']>=3
        delta=old['median_sim']-d['median_sim'] if complete else None
        results.append({'complete':complete,'observed':old['median_sim'],
                        'null':d['median_sim'],'excess':delta,
                        'obs_pairs':old['pair_count'],'null_pairs':d['pair_count'],
                        'observed_sne':old['median_sne'],'null_sne':d['median_sne']})
    if margin(nulls)!=marg:raise ValueError('FIXED_MARGIN_DRIFT final')
    usable=[z for z in results if z['complete']]
    diffs=[x['excess'] for x in usable]
    pos=sum(x>0 for x in diffs)
    pair_summaries=[]
    for pair in combinations(names,2):
        obs= bypair[pair]['observed']; null=bypair[pair]['null']
        a=median(obs) if obs else None
        b=median(null) if null else None
        pair_summaries.append({'pair_1':pair[0],'pair_2':pair[1],
                               'observed_median_beta_sim':a,'null_median_beta_sim':b,
                               'difference_medians':a-b if a is not None and b is not None else None,
                               'observed_pair_draws':len(obs),'null_pair_draws':len(null)})
    enough=len(usable)==draws
    passed=enough and pos>=math.ceil(0.95*draws)
    return {
        'status':'ESTIMABLE' if enough else 'INCOMPLETE_PAIRED_SUPPORT',
        'num_projects':len(projects), 'num_cameras':len(rows),
        'positive_camera_taxon_incidences':sum(len(x) for x in rows),
        'distinct_mammal_taxa_positive_cameras':len(marg[1]),
        'eligible_project_camera_counts':{p:len(projects[p]) for p in names},
        'fixed_cameras_per_project':CAMERAS_PER_DRAW,
        'trades_accepted_initial':burned,
        'trades_accepted_between':accepted,
        'margins_preserved':True,
        'pair_count_expected':pairs_expected,
        'complete_paired_draws':len(usable),
        'paired_draws_total':len(results),
        'observed_gt_null_draws':pos,
        'observed_beta_sim_median':median(x['observed'] for x in usable) if usable else None,
        'null_beta_sim_median':median(x['null'] for x in usable) if usable else None,
        'observed_beta_sne_median':median(x['observed_sne'] for x in usable) if usable else None,
        'null_beta_sne_median':median(x['null_sne'] for x in usable) if usable else None,
        'median_paired_excess':median(diffs) if diffs else None,
        'paired_excess_descriptive_5_95_range':quantiles(diffs),
        'primary_190_of_200_rule_passed':passed,
        'pair_summaries':pair_summaries,
    }


def run(deploy_path,seq_path,description_path):
    provenance=verify_sources({'deployment':deploy_path,'sequence':seq_path,'description':description_path})
    by_id,cameras,dep_qc=read_deployments(deploy_path)
    response_qc=read_sequence_labels(seq_path,by_id,cameras)
    regions,site_qc=prepare_regions(cameras)
    reports={name:per_region(name,regions[name]) for name in REGIONS}
    ready=all(r['status']=='ESTIMABLE' for r in reports.values())
    both=ready and all(r['primary_190_of_200_rule_passed'] for r in reports.values())
    one=ready and any(r['primary_190_of_200_rule_passed'] for r in reports.values())
    status=('REGION_NULL_EXCESS_BOTH_REGIONS' if both else
            'REGION_NULL_EXCESS_ONE_REGION' if one else
            'NO_REGION_NULL_EXCESS' if ready else 'INSUFFICIENT_REGION_SUPPORT')
    return {
        'schema_version':1,
        'date':'2026-11-17',
        'status':status,
        'source':provenance,
        'fixed_method':{'meridian_west_east_degrees':-100,'min_days':MIN_DAYS,
                        'min_cameras_per_project':MIN_CAMERAS,'cameras_per_project_draw':CAMERAS_PER_DRAW,
                        'min_positive_cameras_per_species':SPECIES_PER_PROJECT_MIN_CAMERAS,
                        'paired_draws_per_region':DRAWS,
                        'burnin_proposals_per_camera':BURN_PER_ROW,
                        'between_draw_proposals_per_camera':BETWEEN_PER_ROW,
                        'primary_threshold':190},
        'quality':{'deployment':dep_qc,'response':response_qc,'site':site_qc},
        'regional_results':reports,
        'limits':{'not_detection_corrected':True,'not_ecologically_causal':True,
                  'not_a_pvalue_or_confidence_interval':True,
                  'curveball_uniform_mixing_not_proven':True,
                  'no_species_camera_or_sequence_ids_exported':True,
                  'not_eSDM_fit_or_E5_G4_qualified':True,
                  'previous_E4_E5_E7_E7C_Safari14_C1_unmodified':True}}


def main():
    p=argparse.ArgumentParser()
    for key in ['deployment','sequence','description','out']:
        p.add_argument('--'+key,required=True,type=Path)
    args=p.parse_args()
    try:
        result=run(args.deployment,args.sequence,args.description)
    except (ValueError, OSError, csv.Error) as exc:
        reason=str(exc)
        prefix=reason.split(':',1)[0]
        allowed={'TRANSPORT_OR_SOURCE_STOP','DEPLOYMENT_SCHEMA_STOP',
                 'RESPONSE_SCHEMA_STOP','INSUFFICIENT_REGION_SUPPORT'}
        result={'schema_version':1,'date':'2026-11-17',
                'status':prefix if prefix in allowed else 'TECHNICAL_STOP',
                'reason':reason,
                'inference_limits':{'no_positive_result_claimed':True,
                                    'model_fit_performed':False,
                                    'previous_results_changed':False}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],
                      'regions':{r:{k:v.get(k) for k in ('status','num_projects','num_cameras','complete_paired_draws','observed_gt_null_draws','median_paired_excess')} for r,v in result.get('regional_results',{}).items()}},sort_keys=True))

if __name__=='__main__':
    main()
