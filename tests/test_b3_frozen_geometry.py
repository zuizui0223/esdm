"""Archive regression checks; protects original aggregate metadata receipt."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1]/'docs/replication/B3_BARRY_GEOMETRY_RESULT.json'
SHA='0de305d3bbe622b480c7edc1e76055b36520b08ee13a8cc48dc65234175ce00f'

def test_original_bytes():assert hashlib.sha256(P.read_bytes()).hexdigest()==SHA

def test_study_geometry_not_biological_result():
 d=json.loads(P.read_text());assert d['status']=='METADATA_GEOMETRY_EVALUATED_NOT_ECOLOGICAL_EFFECT'
 assert d['biological_response_fields_accessed'] is False
 assert d['original_E5_qualified_count_unchanged']==0

def test_critical_outcome_counts():
 d=json.loads(P.read_text());assert d['camera_rows']==1240 and d['dog_segment_rows']==5037
 assert d['ecoregions_with_both_methods']==4
 assert d['shared_ecoregion_sample_unit_keys_total']==0
 assert all(x['shared_sample_unit_keys']==0 for x in d['per_ecoregion_sampling_only'])
