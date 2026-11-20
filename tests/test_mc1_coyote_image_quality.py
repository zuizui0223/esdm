"""Source-independent synthetic checks for MC1. No published animal row opened."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import io
import math
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'scripts'/'mc1_coyote_image_quality.py'
spec=importlib.util.spec_from_file_location('mc1_quality',PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HEADER='new_file_name,blur,File_name_order,Mange_signs_present,In_color,Season,Year,propbodyvis,surveyid,site,date\n'
def source_row(*, name='x',blur='20',y='1',color='1',season='Fall',year='2010',body='0.2',site='s1'):
    return f'{name},{blur},1,{y},{color},{season},{year},{body},survey01,{site},2010-09-01\n'

def fake_records(nsites=114,nper=35,flip_holdout=False):
    rows=[]
    for i in range(nsites):
        site=f'fixed_site_{i:03d}'
        for j in range(nper):
            # image quality is predictive, not a hidden station identity
            y=int(j%5<2)
            if flip_holdout and m.split_site(site)=='validation':
                blur=4 if y else 120
            else: blur=120 if y else 4
            rows.append({'site':site,'year':2010+j%4,'season':m.SEASONS[(j+i)%4],
                         'y':y,'blur':blur,'body':.45 if blur==120 else .10,'color':j%2})
    return rows

def test_git_blob_hash_protocol():
    s=b'abc'
    expected=hashlib.sha1(b'blob 3\0abc').hexdigest()
    assert m.git_blob_sha(s)==expected

def test_wrong_byte_size_stops_before_animal():
    with pytest.raises(ValueError,match='SOURCE_SIGNATURE_STOP'):
        m.check_source(b'synthetic')

def test_header_and_codes_parse():
    r=m.parse_source((HEADER+source_row()).encode())
    assert len(r)==1 and r[0]['y']==1 and r[0]['blur']==20

def test_bool_codes_accepted_for_existing_synthetic():
    r=m.parse_source((HEADER+source_row(y='TRUE',color='false')).encode())
    assert r[0]['y']==1 and r[0]['color']==0

def test_missing_features_not_missing_target():
    r=m.parse_source((HEADER+source_row(blur='NA',body='NA',color='NA')).encode())
    assert r[0]['blur'] is None and r[0]['body'] is None and r[0]['color'] is None

def test_missing_target_rejected():
    with pytest.raises(ValueError,match='invalid mange signs'):
        m.parse_source((HEADER+source_row(y='NA')).encode())

def test_bad_body_fraction_rejected():
    with pytest.raises(ValueError,match='body fraction'):
        m.parse_source((HEADER+source_row(body='1.5')).encode())

def test_negative_blur_rejected():
    with pytest.raises(ValueError,match='negative blur'):
        m.parse_source((HEADER+source_row(blur='-2')).encode())

def test_bad_season_rejected():
    with pytest.raises(ValueError,match='invalid season'):
        m.parse_source((HEADER+source_row(season='Autumn')).encode())

def test_duplicate_image_names_rejected():
    with pytest.raises(ValueError,match='duplicate image'):
        m.parse_source((HEADER+source_row()+source_row(site='s2')).encode())

def test_duplicate_sites_allowed_but_split_grouped():
    rows=fake_records(nsites=114,nper=3)
    split=m.split_records(rows)
    assert {r['site'] for r in split['discovery']}.isdisjoint({r['site'] for r in split['validation']})
    assert len(split['discovery'])+len(split['validation'])==len(rows)

def test_split_determinism_and_sha_prefix():
    s='new_site'
    v=hashlib.sha256((m.SPLIT_SALT+s).encode()).digest()[0]
    assert m.split_site(s)==('validation' if v<51 else 'discovery')

def test_zero_year_variance_no_nan():
    rows=fake_records(5,5)
    for r in rows:r['year']=2020
    cfg=m.fit_feature_encoding(rows)
    x=m.features(rows,cfg,False)
    assert all(math.isfinite(v) for row in x for v in row)
    assert all(row[0]==0 for row in x)

def test_train_only_imputation_no_validation_contamination():
    rows=fake_records(2,4)
    cfg=m.fit_feature_encoding(rows)
    med=cfg['medians']['blur']
    altered=[dict(x,blur=1e9) for x in rows]
    assert m.features(rows,cfg,True)!=m.features(altered,cfg,True)
    assert cfg['medians']['blur']==med

def test_support_gate_rejects_small_dataset():
    support,pas=m.support_check(m.split_records(fake_records(8,4)))
    assert not pas and support['discovery']['images']+support['validation']['images']==32

def test_cluster_bootstrap_constant_gain():
    rows=[{'site':'a','y':1},{'site':'a','y':1},{'site':'b','y':1}]
    ci=m.station_bootstrap(rows,[.0,.0,.0],[1.,1.,1.],100,5)
    assert ci==[1.,1.]

def test_quality_improves_unseen_station_data():
    r=m.evaluate(fake_records())
    assert r['support']['discovery']['site_count']>=60
    assert r['support']['validation']['site_count']>=12
    assert r['status']=='MC1_POSITIVE_HELDOUT_IMAGE_LABEL_PREDICTION'
    assert r['primary']['heldout_brier_gain']>0.005
    assert r['primary']['site_cluster_bootstrap_95_interval'][0]>0

def test_reversed_heldout_image_relationship_is_negative():
    r=m.evaluate(fake_records(flip_holdout=True))
    assert r['status']=='MC1_NEGATIVE_HELDOUT_IMAGE_LABEL_PREDICTION'
    assert r['primary']['heldout_brier_gain'] < -.005

def test_perfect_equality_percentile():
    assert m._percentile_sorted([.0,.0,.0],.5)==0

def test_no_source_ids_in_result():
    result=m.evaluate(fake_records())
    output=str(result)
    assert 'fixed_site_' not in output
    assert result['limits']['not_E5_G4']
