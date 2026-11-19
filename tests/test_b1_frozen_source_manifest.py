"""Regression guard for archived one-shot metadata opening, no wildlife data."""
from pathlib import Path
import hashlib, json

SOURCE=Path(__file__).resolve().parents[1]/'docs/replication/B1_BARRY_CLARE_SOURCE_MANIFEST_RESULT.json'
SHA='ed5cb00889242276b57c933d9f7ea8336a78cecb5eefd16c983db5a5468b8d06'

def test_original_artifact_result_bytes_unchanged():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA

def test_no_covered_animal_response_opened():
    r=json.loads(SOURCE.read_text())
    assert r['animal_response_opened'] is False
    assert r['figshare']['response_rows_opened']==0 and r['dryad']['response_rows_opened']==0
    assert r['figshare']['original_data_files_downloaded']==0

def test_five_source_files_match_published_immutable_metadata():
    r=json.loads(SOURCE.read_text())
    f={x['name']:x for x in r['figshare']['manifest']['files']}
    assert r['figshare']['status']=='PUBLIC_MANIFEST_PRESENT'
    assert len(f)==5
    assert f['CamStations_Ecosphere.csv']['file_id']==31117351
    assert f['DogTracks_Ecosphere.csv']['file_id']==31117348
    assert f['WestOR_grid_Ecosphere.csv']['file_id']==31117429

def test_clare_manifest_not_falsely_inferred():
    r=json.loads(SOURCE.read_text())
    assert r['dryad']['status']=='DATASET_METADATA_PRESENT_FILES_NOT_ENUMERATED'
    assert r['dryad']['manifest']['file_count'] is None
    assert r['original_E5_qualified_count_unchanged']==0
