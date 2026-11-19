"""Synthetic-only test of Barry survey metadata extraction (not outcomes)."""
import pytest
from scripts import barry_region_method_geometry as g


def c(unit='A',eco='1',device='C1',season='summer'):
 return {'Sample Unit':unit,'EcoProvence_number':eco,'Camera #':device,'season':season,
         'min_date':'2020-01-01','max_date':'2020-02-01','operating_days':'21'}

def d(unit='A',eco='1'):
 return {'SampleUnit':unit,'EcoProvence_number':eco,'SegmentID':'s1'}

def test_exact_shared_key():
 r=g.compute([c('A','1')],[d('A','1')]);assert r['shared_ecoregion_sample_unit_keys_total']==1
 assert r['ecoregions_with_both_methods']==1

def test_false_overlap_different_region():
 r=g.compute([c('A','1')],[d('A','2')]);assert r['shared_ecoregion_sample_unit_keys_total']==0
 assert r['ecoregions_with_both_methods']==0

def test_whitespace_normalization_only():
 r=g.compute([c(' A ',' 1 ')],[d('A','1')]);assert r['shared_ecoregion_sample_unit_keys_total']==1

def test_camera_device_can_move():
 r=g.compute([c('A','1','C1'),c('B','1','C1')],[d('A','1')]);assert r['camera_hardware_ids_mapped_to_gt1_unit']==1

def test_same_sample_unit_across_ecoregions_is_not_assumed_same_place():
 r=g.compute([c('A','1'),c('A','2')],[d('A','1'),d('A','2')]);assert r['shared_ecoregion_sample_unit_keys_total']==2
 assert r['camera_sample_unit_strings_in_multiple_ecoregions']==1

def test_blank_missing_rows_counted():
 r=g.compute([c('', '1'),c('A','1')],[d('', '1'),d('A','1')]);assert r['camera_rows_missing_unit_or_region']==1
 assert r['dog_rows_missing_unit_or_region']==1

def test_no_source_response_fields_in_allowed_metadata():
 assert not any(name in g.PROHIBITED for group in g.ALLOWED.values() for name in group)

def test_season_availability_not_invented_from_dog():
 r=g.compute([c('A')],[d('A')]);assert r['dog_event_time_available_in_published_header'] is False

def test_multiple_regions_coverage_summary():
 cams=[c(str(i),'1',f'C{i}') for i in range(11)]+[c(str(i),'2',f'D{i}') for i in range(11)]
 dogs=[d(str(i),'1') for i in range(11)]+[d(str(i),'2') for i in range(11)]
 r=g.compute(cams,dogs);assert r['ecoregions_with_both_ge10_and_ge3_shared']==2

def test_source_mismatch_no_data_access(tmp_path):
 p=tmp_path/'foo.csv';p.write_text('Sample Unit,EcoProvence_number\nA,1\n')
 assert g.run(p,p)['status']=='METADATA_SOURCE_OR_JOIN_SCHEMA_STOP'

def test_metadata_never_claims_e5_qualification():
 r=g.compute([c()],[d()]);assert r['original_E5_qualified_count_unchanged']==0
 assert not r['G4_independent_camera_passage_reference_established']
