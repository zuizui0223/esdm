"""Only synthetic correctness tests; original wildlife sequences are never loaded."""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
import random
import tempfile

import pytest

from scripts.neon_c2_region_pool_null import (
    beta, sampled_species, margin, trade, quantiles,
    per_region, prepare_regions, read_deployments, read_sequence_labels,
    samples, verify_sources, DRAWS, CAMERAS_PER_DRAW, SEEDS,
)


def make_cam(place,lon,sp):
    return {'place':place,'lon':lon,'lat':40.0,'coords':[(lon,40.0)],
            'ids':{place},'species':set(sp)}


def make_region(prefix,lon,n=22):
    return {f'{prefix}{k}':[make_cam(f'{prefix}{k}_cam{i:02}',lon+i*0.0001,
                        ['Species alpha',f'Project{k} species'])
                     for i in range(n)] for k in range(3)}


def test_baselga_formula_and_undefined_zero_denominator():
    assert beta({'a','b'},{'a','c'})==(0.5,0)
    sim,sne=beta({'a','b'},{'a'})
    assert sim==0
    assert sne==pytest.approx(1/3)
    assert beta(set(),{'a'}) is None
    assert beta(set(),set()) is None


def test_samples_are_frozen_without_replacement_and_stable():
    projects=make_region('S',-80)
    a=samples(projects,n=9)
    assert a==samples(projects,n=9)
    assert len(a)==9
    for draw in a:
        for ids in draw.values():
            assert len(ids)==CAMERAS_PER_DRAW
            assert len(set(ids))==CAMERAS_PER_DRAW


def test_species_positive_on_two_distinct_cameras():
    assert sampled_species([{'A'},{'A','B'},{'B'}],[0,1])=={'A'}
    assert sampled_species([{'A'},{'A','B'},{'B'}],[0,1,2])=={'A','B'}


def test_margin_preservation_and_row_subset_invariance():
    rows=[{'zebra','lion'},{'zebra','buffalo'},{'lion','wildebeest'},set(),{'lion'}]
    orig=margin(rows)
    rng=random.Random(20261117)
    assert sum(trade(rows,rng) for _ in range(1500))>10
    assert margin(rows)==orig
    assert rows[3]==set()


def test_region_conditioning_west_east_and_rejection_of_meridian_crossing():
    cameras={}
    for label,lon in (('EastSite',-80),('WestSite',-115)):
        for i in range(22):
            cameras[(label,f'c{i}')]=make_cam(f'c{i}',lon,['Species alpha'])
    regions,qc=prepare_regions(cameras)
    assert qc['eligible_projects_by_region']=={'East':1,'West':1}
    assert set(regions['West'])=={'WestSite'}
    cameras[('EastSite','c0')]['coords']=[(-101,40)]
    with pytest.raises(ValueError,match='crosses fixed'):
        prepare_regions(cameras)


def test_region_empirical_simpson_null_returns_all_pair_summaries():
    region=make_region('Q',-110,n=20)
    r=per_region('West',region,draws=8,burn=4,between=4)
    assert r['status']=='ESTIMABLE'
    assert r['num_projects']==3
    assert r['num_cameras']==60
    assert r['margins_preserved'] is True
    assert r['pair_count_expected']==3
    assert len(r['pair_summaries'])==3
    assert r['complete_paired_draws']==8
    assert r['trades_accepted_between']>0
    assert r['observed_beta_sim_median']==pytest.approx(0.5)
    assert r['primary_190_of_200_rule_passed'] is False  # deliberately only eight draws


def test_missing_region_three_projects_is_hard_stop():
    r=per_region('East',make_region('F',-80)|{},draws=5,burn=3,between=3)
    assert r['status']=='ESTIMABLE'
    r=per_region('East',dict(list(make_region('F',-80).items())[:2]),draws=5,burn=3,between=3)
    assert r['status']=='INSUFFICIENT_REGION_SUPPORT'


def test_invalid_response_header_rejected_before_records():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'seq.csv'
        p.write_text('deployment_id,sequence_id,species\nx,one,Felis catus\n')
        with pytest.raises(ValueError,match='RESPONSE_SCHEMA_STOP'):
            read_sequence_labels(p,{}, {})


def test_response_species_binomials_domestic_and_duplicates_are_handled():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'seq.csv'
        p.write_text('deployment_id,sequence_id,class,genus,species\n'
                     'x,one,Mammalia,Vulpes,vulpes\n'
                     'x,one,Mammalia,Vulpes,vulpes\n'
                     'x,two,Mammalia,Felis,catus\n'
                     'x,three,Aves,Turdus,migratorius\n'
                     'x,four,Mammalia,Vulpes,sp\n')
        cameras={('A','c1'):{'species':set()}}
        q=read_sequence_labels(p,{'x':{'identity':('A','c1')}},cameras)
        assert cameras[('A','c1')]['species']=={'Vulpes vulpes'}
        assert q['duplicate_deployment_sequence_taxon']==1
        assert q['excluded_domestic']==1
        assert q['excluded_nonmammal']==1
        assert q['excluded_missing_or_invalid_binomial']==1


def test_conflicting_taxonomic_class_is_terminal():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'seq.csv'
        p.write_text('deployment_id,sequence_id,class,genus,species\n'
                     'x,one,Mammalia,Vulpes,vulpes\n'
                     'x,two,Aves,Vulpes,vulpes\n')
        with pytest.raises(ValueError,match='taxonomic class conflicts'):
            read_sequence_labels(p,{'x':{'identity':('A','c1')}},{('A','c1'):{'species':set()}})


def test_deployment_validity_and_duplicate_conflict_is_terminal():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'dep.csv'
        heading='deployment_id,placename,longitude,latitude,start_date,end_date,subproject_name\n'
        p.write_text(heading+'x,cam1,-100.1,40.0,2022-06-01,2022-06-28,W\n'
                    'x,cam1,-100.1,40.0,2022-06-01,2022-06-28,W\n'
                    'y,cam2,-100.1,40.0,2022-06-01,2022-06-05,W\n')
        by_id,cameras,q=read_deployments(p)
        assert len(by_id)==1 and len(cameras)==1
        assert q['identical_duplicate_ids']==1
        assert q['invalid_location_or_short_interval']==1
        p.write_text(heading+'x,cam1,-100.1,40.0,2022-06-01,2022-06-28,W\n'
                    'x,cam2,-100.1,40.0,2022-06-01,2022-06-28,W\n')
        with pytest.raises(ValueError,match='different physical cameras'):
            read_deployments(p)


def test_sha_locked_source_preflight_refuses_wrong_file_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        paths={}
        for key in ('deployment','sequence','description'):
            p=Path(tmp)/key
            p.write_bytes(b'this is not Zenodo source')
            paths[key]=p
        with pytest.raises(ValueError,match='MD5 drift'):
            verify_sources(paths)


def test_quantiles_on_ordered_values_without_cis():
    assert quantiles([]) is None
    assert quantiles([0.2,0.4,0.1,0.3])==[0.1,0.4]
    assert DRAWS==200
    assert SEEDS=={'East':20261118,'West':20261117}
