"""Source-independent correctness; no published mammal sequence or response opened."""
from __future__ import annotations

from datetime import date
from io import StringIO
import csv
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.snapshot_europe_c3_country_prior import (
    clean_species, exposure_days, parse_year, parse_date, parse_projects,
    parse_deployments, parse_sequences, one_year_subsets, choose_roster,
    brier_fit_score, evaluate, guarded_rows, source_guard, FILES, REQUIRED,
    MIN_DAYS, MIN_SPECIES, MIN_PER_COUNTRY, MIN_TRAIN_CAMERAS, MIN_HOLDOUT_CAMERAS,
    SHRINK_CAMERAS, ZIP_SHA256, ZIP_MD5, ZIP_BYTES,
)


def test_source_identity_freeze_requires_published_edmond_v2_bytes(tmp_path):
    f = tmp_path / 'wrong.zip'
    f.write_bytes(b'ZIP magic? never trust extension')
    with pytest.raises(ValueError, match='TRANSPORT_OR_SOURCE_STOP'):
        source_guard(f)
    assert ZIP_SHA256 == '8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54'
    assert ZIP_MD5 == '102a0e35504eaa95c1b59bcd71c42a0d'
    assert ZIP_BYTES == 77352666


def test_calendar_parser_refuses_invalid_dates_and_years():
    assert parse_year('2021') == 2021
    assert parse_year('2022') == 2022
    assert parse_year('2019') is None
    assert parse_year('hey') is None
    assert parse_date('2021-09-11 12:30') == date(2021, 9, 11)
    assert parse_date('2021-02-30') is None
    assert parse_date('') is None
    assert parse_date('2021-11-01Z') == date(2021, 11, 1)


def test_exposure_enforces_common_season_and_exact_day_minimum():
    assert exposure_days(2021,'2021-08-01','2021-09-20') == 20
    assert exposure_days(2021,'2021-10-12','2021-11-15') == 20
    assert exposure_days(2021,'2021-10-13','2021-11-15') == 19
    assert exposure_days(2022,'2022-01-01','2022-08-31') == 0
    assert exposure_days(2022,'2022-11-01','2022-10-01') is None
    assert MIN_DAYS == 20


def test_species_identity_and_domestic_refusal():
    assert clean_species('Vulpes','vulpes') == 'Vulpes vulpes'
    assert clean_species('Homo','sapiens') is None
    assert clean_species('Canis','familiaris') is None
    assert clean_species('Canis','sp.') is None
    assert clean_species('vulpes','vulpes') is None
    assert clean_species('Canis','') is None


def _project(year='2021', id='p', country='DE'):
    return dict(year=year,project_id=id,country_code=country)


def _dep(year='2021',p='p',d='d',cid='camera',array='F',start='2021-09-01',end='2021-10-31',flag='true'):
    return dict(year=year,project_id=p,deployment_id=d,camera_id=cid,
        subproject_name_no_year=array,longitude='10',latitude='50',
        start_date=start,end_date=end,camera_functioning=flag)


def _seq(year='2021',p='p',d='d',sid='s1',genus='Vulpes',species='vulpes',start='2021-09-02',blank='false',klass='Mammalia'):
    return dict(year=year,project_id=p,deployment_id=d,sequence_id=sid,
        genus=genus,species=species,start_time=start,is_blank=blank,**{'class':klass})


def test_conflicting_project_geography_hard_stops():
    with pytest.raises(ValueError,match='conflicting project-country'):
        parse_projects([_project(country='DE'),_project(country='PL')])
    x,qc=parse_projects([_project(country='DE'),_project(country='DE')])
    assert len(x)==1 and qc['exact_duplicate_project']==1


def test_deployment_duplicate_and_coordinate_eligibility():
    projects={(2021,'p'):'DE'}
    good=_dep()
    bad=_dep(d='e',cid='other',start='2021-10-13')
    cam,dep,qc=parse_deployments([good,good,bad],projects)
    assert len(cam)==1 and len(dep)==1
    assert qc['exact_duplicate_deployment']==1
    assert qc['inadequate_or_invalid_exposure']==1
    with pytest.raises(ValueError,match='conflicting deployment identity'):
        parse_deployments([good, dict(good,camera_id='different')],projects)


def test_camera_conflicting_arrays_refuse_and_unknown_functioning_not_falsified():
    projects={(2021,'p'):'DE'}
    with pytest.raises(ValueError,match='conflicting country/array'):
        parse_deployments([_dep(d='1',array='X'),_dep(d='2',array='Y')],projects)
    cams,deps,qc=parse_deployments([_dep(d='1',flag=''),_dep(d='2',cid='other',flag='broken')],projects)
    assert len(cams)==1 and qc['unknown_functioning_retained']==1
    assert qc['explicit_nonfunctioning']==1


def test_sequences_respect_timestamp_mammal_dedup_and_no_focal_selection():
    cams,deps,_=parse_deployments([_dep()],{(2021,'p'):'DE'})
    x = [_seq(),_seq(),_seq(sid='s2',start='2021-12-01'),
         _seq(sid='s3',klass='Aves'),_seq(sid='s4',blank='true'),
         _seq(sid='s5',genus='Felis',species='catus'),_seq(sid='s6',d='no_such')]
    hits,qc=parse_sequences(x,deps)
    assert list(hits.values())==[{'Vulpes vulpes'}]
    assert qc['eligible_recorded_mammal_sequences']==1
    assert qc['duplicate_camera_sequence_species']==1
    assert qc.get('timestamp_outside_deployment',0)+qc.get('invalid_or_outside_window_timestamp',0)==1
    assert qc['blank_sequence']==1
    assert qc['non_mammal']==1
    with pytest.raises(ValueError,match='sequence ID maps'):
        parse_sequences([_seq(d='d',sid='x'),_seq(d='z',sid='x')],deps)


def test_new_array_2022_validation_excludes_repeated_arrays():
    cameras = {(2021,'p','a'):{'year':2021,'array':('DE','forest'),'country':'DE'},
               (2022,'q','b'):{'year':2022,'array':('DE','forest'),'country':'DE'},
               (2022,'q','c'):{'year':2022,'array':('DE','new'),'country':'DE'}}
    t,v,qc=one_year_subsets(cameras,{})
    assert len(t)==1 and len(v)==1
    assert qc['2022_cameras_in_shared_2021_arrays_excluded']==1


def _tiny_crossyear_fixture(ncountries=5,ntrain=50,nval=50,ntaxa=10):
    cams={}; hits={}
    for c in range(ncountries):
        country=f'C{c}'
        for i in range(ntrain):
            key=(2021,country,str(i))
            cams[key]={'year':2021,'country':country,'array':(country,'2021forest')}
            hits[key]={f'Taxon species{j}' for j in range(ntaxa) if (j+i+c)%3 != 0}
        for i in range(nval):
            key=(2022,country,str(i))
            cams[key]={'year':2022,'country':country,'array':(country,'2022forest')}
            hits[key]={f'Taxon species{j}' for j in range(ntaxa) if (j+i+c)%3 != 0}
    return cams,hits


def test_training_taxa_never_selected_using_2022():
    cameras,hits=_tiny_crossyear_fixture(ncountries=5,ntrain=40,nval=40,ntaxa=10)
    t,v,_=one_year_subsets(cameras,hits)
    roster=choose_roster(t,hits)
    assert len(roster)==10
    for cid in v:
        hits[cid].add('Zebrus deliberatelynew')
    assert choose_roster(t,hits)==roster
    assert 'Zebrus deliberatelynew' not in roster


def test_full_holdout_fixture_returns_finite_and_bounded_scores():
    cameras,hits=_tiny_crossyear_fixture(ncountries=5,ntrain=45,nval=45,ntaxa=10)
    out=evaluate(cameras,hits)
    assert out['status'] in {'POSITIVE_DESCRIPTIVE_COUNTRY_PRIOR_TRANSFER','NO_USEFUL_COUNTRY_PRIOR_TRANSFER'}
    assert out['support']['training_cameras']==225
    assert out['support']['new_array_validation_cameras']==225
    assert out['support']['roster_species_count']==10
    scores=out['primary']
    assert 0<=scores['brier_global']<=1
    assert 0<=scores['brier_country_prior']<=1
    assert scores['target_camera_taxon_cells']==2250
    assert scores['qualifying_shared_countries']==5
    assert MIN_PER_COUNTRY==10 and SHRINK_CAMERAS==20


def test_support_failure_not_promoted_as_ecological_negative():
    cameras,hits=_tiny_crossyear_fixture(ncountries=4,ntrain=45,nval=45,ntaxa=8)
    out=evaluate(cameras,hits)
    assert out['status']=='INSUFFICIENT_TRANSFER_SUPPORT'
    assert 'primary' not in out


def test_csv_reader_only_opens_three_declared_members(tmp_path):
    path=tmp_path/'synthetic.zip'
    with ZipFile(path,'w') as z:
        for kind in FILES:
            head=sorted(REQUIRED[kind]); row={c:'x' for c in head}
            stream=StringIO();writer=csv.DictWriter(stream,fieldnames=head)
            writer.writeheader();writer.writerow(row)
            z.writestr(FILES[kind],stream.getvalue())
        z.writestr('DataS1/Snapshot_Europe_2021_2022_images.csv',b'PROHIBITED TO READ')
    with ZipFile(path) as z:
        for kind in FILES:
            assert len(list(guarded_rows(z,kind)))==1
    assert set(FILES)=={'projects','deployments','sequences'}


def test_missing_required_sequence_columns_fail_closed(tmp_path):
    path=tmp_path/'wrong.zip'
    with ZipFile(path,'w') as z:
        z.writestr(FILES['sequences'],'year,project_id,sequence_id\n2021,p,1\n')
    with ZipFile(path) as z:
        with pytest.raises(ValueError,match='RESPONSE_SCHEMA_STOP'):
            list(guarded_rows(z,'sequences'))
