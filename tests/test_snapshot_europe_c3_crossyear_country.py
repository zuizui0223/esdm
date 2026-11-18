"""Synthetic-only C3 tests. NEVER download/open European animal responses."""
from __future__ import annotations

from datetime import date
import io
import math
from pathlib import Path
import random
from zipfile import ZipFile
import pytest

from scripts.snapshot_europe_c3_crossyear_country import (
    PREFIX, MEMBERS, SOURCE_MD5, SOURCE_SHA256, SOURCE_SIZE, SOURCE_FILE_ID,
    MIN_ROSTER_SPECIES, DOMESTIC,
    _calendar, _taxon, _iter_dicts, parse_projects, parse_deployments,
    parse_sequences, select_roster, grouped_cameras, evaluate,
    verify_source,
)


def _csv(rows):
    return ('\n'.join(rows)+'\n').encode()


def _zip(projects=None,deployments=None,sequences=None, extra=None):
    default = {
        'projects':['year,project_id,country_code', '2021,P1,FR','2022,P2,FR'],
        'deployments':['year,project_id,deployment_id,longitude,latitude,start_date,end_date,camera_id,camera_functioning,subproject_name_no_year',
                       '2021,P1,D1,2,48,2021-08-20,2021-10-31,C1,yes,A',
                       '2022,P2,D2,2,48,2022-08-20,2022-10-31,C2,,B'],
        'sequences':['year,project_id,deployment_id,sequence_id,is_blank,class,genus,species,start_time',
                     '2021,P1,D1,S1,false,Mammalia,Vulpes,vulpes,2021-09-10T12:00:00',
                     '2022,P2,D2,S2,false,Mammalia,Vulpes,vulpes,2022-09-12T12:00:00']
    }
    for k,v in (('projects',projects),('deployments',deployments),('sequences',sequences)):
        if v is not None: default[k]=v
    stream=io.BytesIO()
    with ZipFile(stream,'w') as z:
        for name,rows in default.items():z.writestr(MEMBERS[name],_csv(rows))
        z.writestr(PREFIX+'images.csv',b'NEVER_OPEN_THIS_DATA_FILE\n')
        if extra:
            for k,v in extra.items():z.writestr(k,v)
    stream.seek(0)
    return ZipFile(stream)


def test_pinned_source_contract():
    assert SOURCE_SIZE==77352666 and SOURCE_FILE_ID==345505
    assert SOURCE_MD5=='102a0e35504eaa95c1b59bcd71c42a0d'
    assert SOURCE_SHA256=='8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54'


def test_unverified_wrong_source_rejected_before_any_response(tmp_path):
    f=tmp_path/'wrong.zip';f.write_bytes(b'bad')
    with pytest.raises(ValueError,match='SOURCE_STOP'):
        verify_source(f)


def test_correct_header_and_no_image_member_opening():
    with _zip() as z:
        p,_=parse_projects(z)
        d,c,q=parse_deployments(z,p)
        s,qs=parse_sequences(z,d)
    assert len(p)==2 and len(c)==2 and q['eligible_deployments']==2
    assert qs['eligible_sequence_taxon_records']==2
    assert s[(2021,'P1','C1')]=={'Vulpes vulpes'}


def test_exact_year_and_iso_date_parsing():
    assert _calendar('2021-09-30T15:23:40+01:00')==date(2021,9,30)
    assert _calendar('31/09/2021') is None
    assert _calendar('2021-02-30T00:00') is None


def test_mammal_binomial_excludes_uncertain_names():
    assert _taxon({'genus':'Vulpes','species':'vulpes'})=='Vulpes vulpes'
    assert _taxon({'genus':'Lynx','species':'sp.'}) is None
    assert _taxon({'genus':'Canis lupus','species':'lupus'}) is None
    assert 'Homo sapiens' in DOMESTIC


def test_short_deployment_excluded_and_unknown_functioning_retained():
    rows=['year,project_id,deployment_id,longitude,latitude,start_date,end_date,camera_id,camera_functioning,subproject_name_no_year',
          '2021,P1,D1,2,48,2021-10-20,2021-10-31,C1,yes,A',
          '2022,P2,D2,2,48,2022-09-01,2022-10-31,C2,,B']
    with _zip(deployments=rows) as z:
        p,_=parse_projects(z);d,c,q=parse_deployments(z,p)
    assert len(d)==1 and q['insufficient_window_overlap_days']==1
    assert q['eligible_deployments_unknown_functioning']==1


def test_explicit_nonfunctional_camera_excluded():
    rows=['year,project_id,deployment_id,longitude,latitude,start_date,end_date,camera_id,camera_functioning,subproject_name_no_year',
          '2021,P1,D1,2,48,2021-09-01,2021-10-31,C1,broken,A',
          '2022,P2,D2,2,48,2022-09-01,2022-10-31,C2,yes,B']
    with _zip(deployments=rows) as z:
        p,_=parse_projects(z);d,c,q=parse_deployments(z,p)
    assert len(d)==1 and q['explicit_nonfunctioning']==1


def test_conflicting_project_duplicate_is_hard_stop():
    rows=['year,project_id,country_code','2021,P1,FR','2021,P1,DE']
    with _zip(projects=rows) as z:
        with pytest.raises(ValueError,match='conflicting project'):
            parse_projects(z)


def test_exact_project_duplicate_is_deduplicated():
    rows=['year,project_id,country_code','2021,P1,FR','2021,P1,FR']
    with _zip(projects=rows) as z:
        p,q=parse_projects(z)
    assert q['duplicate_exact_projects']==1 and p[(2021,'P1')]=='FR'


def test_conflicting_deployment_duplicate_is_hard_stop():
    head='year,project_id,deployment_id,longitude,latitude,start_date,end_date,camera_id,camera_functioning,subproject_name_no_year'
    rows=[head,'2021,P1,D1,2,48,2021-09-01,2021-10-31,C1,yes,A',
         '2021,P1,D1,3,48,2021-09-01,2021-10-31,C1,yes,A']
    with _zip(deployments=rows) as z:
        p,_=parse_projects(z)
        with pytest.raises(ValueError,match='conflicting deployment'):
            parse_deployments(z,p)


def test_same_physical_camera_multiple_array_is_hard_stop():
    head='year,project_id,deployment_id,longitude,latitude,start_date,end_date,camera_id,camera_functioning,subproject_name_no_year'
    rows=[head,'2021,P1,D1,2,48,2021-09-01,2021-10-31,C1,yes,A',
         '2021,P1,D3,2,48,2021-09-01,2021-10-31,C1,yes,B']
    with _zip(deployments=rows) as z:
        p,_=parse_projects(z)
        with pytest.raises(ValueError,match='physical camera'):
            parse_deployments(z,p)


def test_sequence_conflicting_deployment_link_is_hard_stop():
    rows=['year,project_id,deployment_id,sequence_id,is_blank,class,genus,species,start_time',
          '2021,P1,D1,S1,false,Mammalia,Vulpes,vulpes,2021-09-10',
          '2021,P1,D3,S1,false,Mammalia,Vulpes,vulpes,2021-09-11']
    with _zip(sequences=rows) as z:
        p,_=parse_projects(z);d,_,_=parse_deployments(z,p)
        with pytest.raises(ValueError,match='sequence identity'):
            parse_sequences(z,d)


def test_sequence_duplicate_species_camera_deduplicated():
    rows=['year,project_id,deployment_id,sequence_id,is_blank,class,genus,species,start_time',
          '2021,P1,D1,S1,false,Mammalia,Vulpes,vulpes,2021-09-10',
          '2021,P1,D1,S1,false,Mammalia,Vulpes,vulpes,2021-09-10']
    with _zip(sequences=rows) as z:
        p,_=parse_projects(z);d,_,_=parse_deployments(z,p)
        s,q=parse_sequences(z,d)
    assert s[(2021,'P1','C1')]=={'Vulpes vulpes'}
    assert q['duplicate_sequence_species_camera']==1


def test_sequences_not_within_deployment_are_excluded():
    rows=['year,project_id,deployment_id,sequence_id,is_blank,class,genus,species,start_time',
          '2021,P1,D1,S1,false,Mammalia,Vulpes,vulpes,2021-11-10',
          '2022,P2,D2,S2,false,Mammalia,Vulpes,vulpes,2022-09-12']
    with _zip(sequences=rows) as z:
        p,_=parse_projects(z);d,_,_=parse_deployments(z,p)
        s,q=parse_sequences(z,d)
    assert q['time_outside_verified_deployment_window']==1
    assert not s[(2021,'P1','C1')]


def _synthetic_assemblages(reverse=False, shared_arrays=False, n=50):
    physical={}
    obs={}
    for i in range(5):
        country=f'Z{i}'
        train_group=f'TRAIN_{i}'
        valid_group=train_group if shared_arrays else f'VALID_{i}'
        for year in (2021,2022):
            for ci in range(n):
                cam=(year,f'P_{i}',f'{year}_{i}_{ci}')
                physical[cam]=(country,train_group if year==2021 else valid_group)
                expected=set()
                for j in range(10):
                    in_group=((i+j)%5 < 3)
                    if year==2022 and reverse: in_group=not in_group
                    if in_group:expected.add(f'Genus{j} species')
                obs[cam]=expected
    return physical,obs


def test_training_roster_is_preoutcome_and_crosses_countries():
    physical,obs=_synthetic_assemblages()
    train,hold,_,_=grouped_cameras(physical)
    assert len(train)==len(hold)==250
    assert len(select_roster(train,obs,physical))==10
    # 2022 outcome mutations must not change the 2021 roster.
    altered={k:(set() if k[0]==2022 else set(v)) for k,v in obs.items()}
    assert select_roster(train,obs,physical)==select_roster(train,altered,physical)


def test_positive_country_borrowing_with_true_predictive_transfer():
    physical,obs=_synthetic_assemblages()
    r=evaluate(physical,obs)
    assert r['status']=='POSITIVE_DESCRIPTIVE_COUNTRY_PRIOR_TRANSFER'
    assert r['support']['estimable_shared_countries']==5
    assert r['support']['roster_species_count']==10
    assert r['primary']['target_camera_species_rows']==2500
    assert r['primary']['Brier_gain_G_minus_G_plus_country']>0.15
    assert r['primary']['positive_country_fraction']==1
    assert len(r['countries'])==5
    assert all(not ('camera_id' in row or 'species' in row) for row in r['countries'])


def test_negative_country_borrowing_does_not_rescue():
    physical,obs=_synthetic_assemblages(reverse=True)
    r=evaluate(physical,obs)
    assert r['status']=='NO_USEFUL_COUNTRY_PRIOR_TRANSFER'
    assert r['primary']['Brier_gain_G_minus_G_plus_country']<0
    assert not r['primary']['predeclared_positive_rule_met']


def test_shared_arrays_must_not_enter_validation():
    physical,obs=_synthetic_assemblages(shared_arrays=True)
    result=evaluate(physical,obs)
    assert result['status']=='INSUFFICIENT_TRANSFER_SUPPORT'
    assert result['support']['excluded_shared_array_2022_cameras']==250
    assert result['support']['heldout_new_array_cameras']==0


def test_below_roster_support_has_no_fitted_score():
    physical,obs=_synthetic_assemblages()
    for key in obs:
        obs[key]={s for s in obs[key] if s.startswith(('Genus0','Genus1','Genus2'))}
    result=evaluate(physical,obs)
    assert result['status']=='INSUFFICIENT_TRANSFER_SUPPORT'
    assert 'primary' not in result


def test_countries_without_2021_counterparts_do_not_qualify():
    physical,obs=_synthetic_assemblages()
    for key in list(physical):
        if key[0]==2021 and physical[key][0]=='Z4':
            physical[key]=('Z_OTHER',physical[key][1])
    result=evaluate(physical,obs)
    assert result['status']=='INSUFFICIENT_TRANSFER_SUPPORT'
    assert result['support']['estimable_shared_countries']==4
