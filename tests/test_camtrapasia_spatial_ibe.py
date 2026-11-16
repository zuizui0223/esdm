"""Synthetic-only checks for CamTrapAsia independent spatial ecological test.

Never reads real mammal records or redefines frozen selection after results.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from scripts.camtrapasia_spatial_ibe import (
    ENV, META_REQUIRED, CAP_REQUIRED, analyze, beta_sim, center_scale,
    environmental_scale, haversine, read_capture_sets, read_metadata,
    ridge_fit, predict, score, split_group, solve_linear,
)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row(key='study-1', country='Testland', landscape='Region 1', effort=1000, cameras=20, v=30):
    r = {f:'' for f in META_REQUIRED}
    r.update(survey_id=key,country=country,landscape=landscape,
             effort=effort,n_cameras=cameras,Y_lat=4.5,X_long=102.5,Source='synthetic',
             forest_cover_20km=v,precipitation_20km=2000,
             temperature_20km=25,human_footprint_20km=10)
    return r


def test_observability_gate_is_metadata_only(tmp_path):
    p=tmp_path/'metadata.csv'
    write_csv(p,META_REQUIRED,[row(),row('low-effort',effort=499),row('few-cams',cameras=9),row('finite',v=65)])
    data,q=read_metadata(p)
    assert set(data)=={'study-1','finite'}
    assert q['metadata_total']==4
    assert q['metadata_excluded']['effort_camera_threshold']==2


def test_duplicate_metadata_id_is_a_terminal_stop(tmp_path):
    p=tmp_path/'meta.csv'
    write_csv(p,META_REQUIRED,[row(),row()])
    with pytest.raises(ValueError,match='duplicate'):
        read_metadata(p)


def test_mammal_species_and_two_record_threshold(tmp_path):
    p=tmp_path/'captures.csv'
    rows=[]
    def cap(name,n,klass='Mammalia',level='species',study='study-1'):
        r={f:'' for f in CAP_REQUIRED}
        r.update(survey_id=study,records=n,binomial_verified=name,**{'class':klass},taxonomic_level=level)
        return r
    rows.extend([cap('Panthera pardus',1),cap('Panthera pardus',1),cap('Vulpes vulpes',2),
                 cap('Bos taurus',3),cap('Corvus corax',8,klass='Aves'),
                 cap('Unknown',19,level='genus'),cap('Meles meles',4,study='other')])
    write_csv(p,CAP_REQUIRED,rows)
    sets,stats=read_capture_sets(p,{'study-1'})
    assert sets['study-1']=={'Panthera pardus','Vulpes vulpes','Bos taurus'}
    assert stats['not_mammal']==1 and stats['not_eligible_study']==1


def test_baselga_turnover_is_symmetric_and_nestedness_invariant():
    assert beta_sim({'a','b'},{'a','c'})==.5
    assert beta_sim({'a','b'},{'a'})==0
    assert beta_sim({'a','b'},{'c','d'})==1
    assert beta_sim(set(),{'a'}) is None


def test_haversine_rough_one_degree_and_split_determinism():
    a={'lat':0.0,'lon':0.0,'country':'A','landscape':'B'}
    b={'lat':0.0,'lon':1.0,'country':'A','landscape':'B'}
    assert 110 < haversine(a,b) < 112
    assert split_group(a)==split_group(b)


def test_constant_environment_does_not_leak_artificial_distance():
    s=[{'env':(10.,20.,30.,40.)},{'env':(10.,30.,30.,50.)}]
    centers=environmental_scale(s)
    assert centers[0][1] is None and centers[2][1] is None
    assert centers[1][1] is not None and centers[3][1] is not None


def test_ridge_fit_handles_constant_predictor_and_predicts_in_bounds():
    rows=[{'y':y,'x':[float(i),0.0,float(i)],'same_country':True}
          for i,y in enumerate((0,.15,.3,.45,.6,.75,.9))]
    f=ridge_fit(rows,True)
    assert len(f['coef'])==3
    assert 0 <= predict(f,{'x':[100,0,100]}) <= 1
    assert 0 <= score(f,rows) <= 1
    assert solve_linear([[2.,1.],[1.,2.]],[3.,3.])==pytest.approx([1,1])


def test_insufficient_transfer_support_does_not_fit_or_relax():
    metadata={'x':{'id':'x','country':'A','landscape':'B','source':'S','effort':1000,
                   'lat':0,'lon':0,'env':(1,2,3,4)}}
    result=analyze(metadata,{'x':{'a','b','c','d','e'}})
    assert result['status']=='INSUFFICIENT_TRANSFER_SUPPORT'
    assert 'primary' not in result