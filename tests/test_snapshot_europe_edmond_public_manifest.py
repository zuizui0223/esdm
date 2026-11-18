"""Pure synthetic-only published-metadata schema contract tests."""
import copy
import pytest
from scripts.snapshot_europe_edmond_public_manifest import extract_public_manifest


def _stub():
    return {'status':'OK','data':{'persistentId':'doi:10.17617/3.7YLWMU',
       'latestVersion':{'versionState':'RELEASED','versionNumber':2,
       'versionMinorNumber':0,'files':[
         {'label':'supplement.zip','dataFile':{'id':501,'filesize':99,
             'checksum':{'type':'MD5','value':'a'*32}}},
         {'label':'readme.txt','dataFile':{'id':502,'filesize':14}},
       ]}}}

def test_valid_public_metadata_without_data_rows():
    x=extract_public_manifest(_stub())
    assert x['status']=='EDMOND_PUBLIC_METADATA_READ_NO_RESPONSE'
    assert x['version']=='2.0' and x['single_unrestricted_zip']
    assert x['eligible_zip_file_ids']==[501]
    assert x['source_rows_opened']==0 and not x['animal_data_read']
    assert not x['E5_G4_pass']

@pytest.mark.parametrize('edit',[lambda x:x.update(status='ERROR'),
  lambda x:x['data'].update(persistentId='doi:other'),
  lambda x:x['data']['latestVersion'].update(versionState='DRAFT'),
  lambda x:x['data']['latestVersion'].update(files=[]),
  lambda x:x['data']['latestVersion']['files'][0]['dataFile'].update(id='abc'),
  lambda x:x['data']['latestVersion']['files'][0]['dataFile'].update(filesize=-1),
  lambda x:x['data']['latestVersion']['files'][0]['dataFile'].update(checksum={'type':'MD5','value':'x'}),
])
def test_corrupt_metadata_rejected(edit):
    x=_stub();edit(x)
    with pytest.raises(ValueError):extract_public_manifest(x)

def test_restricted_zip_is_not_autodownloaded():
    x=_stub();x['data']['latestVersion']['files'][0]['restricted']=True
    y=extract_public_manifest(x)
    assert y['eligible_zip_file_ids']==[] and not y['single_unrestricted_zip']

def test_two_zips_not_silently_selected():
    x=_stub();x['data']['latestVersion']['files'].append({'label':'other.zip',
                       'dataFile':{'id':503,'filesize':100}})
    y=extract_public_manifest(x)
    assert len(y['eligible_zip_file_ids'])==2 and not y['single_unrestricted_zip']

def test_dataverse_identity_in_latest_version_is_supported():
    x=_stub()
    x['data'].pop('persistentId')
    x['data']['latestVersion']['datasetPersistentId']='doi:10.17617/3.7YLWMU'
    assert extract_public_manifest(x)['single_unrestricted_zip']

def test_dataverse_identity_as_components_is_supported():
    x=_stub()
    x['data'].pop('persistentId')
    x['data'].update(protocol='doi',authority='10.17617',identifier='3.7YLWMU')
    assert extract_public_manifest(x)['status']=='EDMOND_PUBLIC_METADATA_READ_NO_RESPONSE'

def test_other_canonical_doi_is_rejected():
    x=_stub()
    x['data'].pop('persistentId')
    x['data']['latestVersion']['datasetPersistentId']='doi:10.17617/WRONG'
    with pytest.raises(ValueError):
        extract_public_manifest(x)
