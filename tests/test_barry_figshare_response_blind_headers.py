"""Synthetic B2 tests; no original biological response values."""
import hashlib
import pytest
from scripts import barry_figshare_response_blind_headers as b

def fixture(tmp_path,text='station,ecoregion,date,method,species\none,a,2020,camera,p\n'):
 p=tmp_path/'demo.csv'; raw=text.encode();p.write_bytes(raw)
 pin=('demo.csv',1,len(raw),hashlib.md5(raw).hexdigest())
 return p,pin

def test_header_only(tmp_path):
 p,pin=fixture(tmp_path);x=b.inspect_header(p,pin)
 assert x['number_of_columns']==5 and x['data_rows_parsed']==0
 assert 'ecoregion' in x['schema_keyword_matches']['ecoregion']

def test_md5_error(tmp_path):
 p,pin=fixture(tmp_path)
 with pytest.raises(ValueError,match='MD5'):b.inspect_header(p,(*pin[:3],'0'*32))

def test_size_error(tmp_path):
 p,pin=fixture(tmp_path)
 with pytest.raises(ValueError,match='SIZE'):b.inspect_header(p,(pin[0],pin[1],pin[2]+1,pin[3]))

def test_duplicate_cols(tmp_path):
 p,pin=fixture(tmp_path,'site,site\nx,y\n')
 with pytest.raises(ValueError,match='DUPLICATE'):b.inspect_header(p,pin)

def test_blank_cols(tmp_path):
 p,pin=fixture(tmp_path,'site,,dog\nx,y,z\n')
 with pytest.raises(ValueError,match='BLANK'):b.inspect_header(p,pin)

def test_unterminated(tmp_path):
 p,pin=fixture(tmp_path,'site,camera')
 with pytest.raises(ValueError,match='UNTERMINATED'):b.inspect_header(p,pin)

def test_semicolon(tmp_path):
 p,pin=fixture(tmp_path,'site;camera;dog\nx;y;z\n')
 assert b.inspect_header(p,pin)['header_names']==['site','camera','dog']

def test_bom(tmp_path):
 p,pin=fixture(tmp_path,'\ufeffsite,camera\nx,1\n')
 assert b.inspect_header(p,pin)['header_names']==['site','camera']

def test_no_response_leak(tmp_path):
 p,pin=fixture(tmp_path,'site,camera\nPRIVATE_ANIMAL_RECORD,PUBLIC\n')
 assert 'PRIVATE_ANIMAL_RECORD' not in str(b.inspect_header(p,pin))

def test_missing_path(tmp_path):
 with pytest.raises(ValueError,match='MISSING'):
  b.inspect_header(tmp_path/'missing',('missing',1,4,'x'))

def test_run_stop_honest(tmp_path):
 r=b.run(tmp_path/'wrong',tmp_path/'wrong',tmp_path/'wrong')
 assert r['status']=='SOURCE_OR_HEADER_STOP'
 assert r['animal_response_rows_parsed']==0 and r['not_E5_qualified']
