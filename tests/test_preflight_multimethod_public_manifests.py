import io, json
import pytest
from scripts.preflight_multimethod_public_manifests import (
 FIG_URL, DRY_URL,FIG_DOI,DRY_DOI, figshare_manifest, dryad_manifest, get_json_metadata,run)


def fig():
 return {'id':16821361,'doi':FIG_DOI,'files':[{'id':11,'name':'fisher_data.RData','size':150,'computed_md5':'abc'}]}


def dry():
 return {'identifier':'doi:'+DRY_DOI,'versionNumber':1,'_links':{'stash:version':{'href':'x'}}}


def test_fig_listing():
 x=figshare_manifest(fig());assert x['file_count']==1 and x['files'][0]['file_id']==11

def test_fig_wrong_id():
 x=fig();x['id']=16821362
 with pytest.raises(ValueError):figshare_manifest(x)

def test_fig_wrong_doi():
 x=fig();x['doi']='10.6084/something-else'
 with pytest.raises(ValueError):figshare_manifest(x)

def test_fig_missing_files():
 x=fig();x.pop('files');assert figshare_manifest(x)['status']=='FILE_LIST_NOT_AVAILABLE'

def test_fig_malformed_file():
 x=fig();x['files'][0]['size']='BAD'
 with pytest.raises(ValueError):figshare_manifest(x)

def test_dry_metadata_not_false_qualified():
 x=dryad_manifest(dry());assert x['status']=='DATASET_METADATA_PRESENT_FILES_NOT_ENUMERATED' and x['file_count'] is None

def test_dry_file_listing():
 x=dry();x['files']=[{'filename':'MartenOccupancyEncounters.csv','size':5360}]
 assert dryad_manifest(x)['files'][0]['name']=='MartenOccupancyEncounters.csv'

def test_dry_wrong_identity():
 x=dry();x['identifier']='not the source'
 with pytest.raises(ValueError):dryad_manifest(x)

def test_source_url_allowlist():
 with pytest.raises(ValueError):get_json_metadata('https://files.figshare.com/animal.csv')

def test_run_success_no_data_download():
 def opener(req,timeout):
  o=fig() if req.full_url==FIG_URL else dry()
  return io.BytesIO(json.dumps(o).encode())
 x=run(opener)
 assert x['figshare']['status']=='PUBLIC_MANIFEST_PRESENT'
 assert x['dryad']['status']=='DATASET_METADATA_PRESENT_FILES_NOT_ENUMERATED'
 assert x['figshare']['response_rows_opened']==x['dryad']['response_rows_opened']==0
 assert x['figshare']['original_data_files_downloaded']==0

def test_run_404_does_not_crash_or_claim_success():
 def opener(req,timeout): raise OSError('test simulated timeout')
 x=run(opener)
 assert x['figshare']['status']==x['dryad']['status']=='METADATA_TRANSPORT_OR_SCHEMA_STOP'
 assert not x['animal_response_opened']

def test_metadata_size_limit():
 def opener(req,timeout):return io.BytesIO(b'x'*6000001)
 with pytest.raises(ValueError,match='6MB'):get_json_metadata(FIG_URL,opener)
