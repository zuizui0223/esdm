"""All tests use fabricated ZIPs; no Europe observations or ZIP download."""
from __future__ import annotations
import json
import zipfile
from pathlib import Path
import pytest
from snapshot_europe_public_header_gate import inspect_archive, tabular_header


def _archive(tmp_path:Path, members:dict[str,bytes])->Path:
    path=tmp_path/'test.zip'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in members.items():z.writestr(name,data)
    return path

def test_only_first_header_line_read(tmp_path):
    p=_archive(tmp_path,{'meta/deployments.csv':b'id,year,lat\nSecret_Camera,2021,44.2\n',
                         'seq/observations.tsv':b'species\tdate\nSECRET_SPECIES\t2022\n',
                         'media/secret.jpg':b'abc'})
    r=inspect_archive(p,'https://test.invalid/snapshot.zip')
    assert r['status']=='RESPONSE_BLIND_HEADER_SCREEN_COMPLETE'
    assert r['raw_rows_opened']==0 and not r['biology_values_opened']
    assert len(r['tabular_headers'])==2
    assert r['tabular_headers'][0]['header_columns']==['id','year','lat']
    assert r['tabular_headers'][1]['header_columns']==['species','date']
    dumped=json.dumps(r)
    assert 'Secret_Camera' not in dumped and 'SECRET_SPECIES' not in dumped
    assert 'media/secret.jpg' not in dumped

def test_no_csv_is_explicit_stop(tmp_path):
    r=inspect_archive(_archive(tmp_path,{'some.rds':b'blob'}),'https://test.invalid')
    assert r['status']=='SCHEMA_UNAVAILABLE_NO_CSV_OR_TSV'

def test_bom_and_quoted_headers():
    assert tabular_header(b'\xef\xbb\xbf"site,id",x','csv'.replace('csv','.csv'))==['site,id','x']

@pytest.mark.parametrize('header',[b'a,,b',b'a,b\x00',b'',b'\xff'])
def test_bad_headers_fail(header):
    with pytest.raises(ValueError):tabular_header(header,'.csv')

def test_reject_unsafe_names(tmp_path):
    with pytest.raises(ValueError,match='unsafe'):
        inspect_archive(_archive(tmp_path,{'../bad.csv':b'a,b\n1,2\n'}),'https://test.invalid')

def test_reject_unterminated_csv_header(tmp_path):
    with pytest.raises(ValueError,match='unterminated'):
        inspect_archive(_archive(tmp_path,{'x.csv':b'field_one,field_two'}),'https://test.invalid')

def test_reject_text_not_archive(tmp_path):
    p=tmp_path/'notzip';p.write_text('HTML ERROR 401')
    with pytest.raises(ValueError):inspect_archive(p,'https://test.invalid')
