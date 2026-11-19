"""Original B2 JSON schema receipt, no animal response values."""
from pathlib import Path
import hashlib,json
F=Path(__file__).resolve().parents[1]/'docs/replication/B2_BARRY_HEADER_RESULT.json'
H='6499f3871a87d5c90141eafe4d99ba7b72585a7ecfc45d50a69f3ffd116847cc'

def test_original_json_digest():assert hashlib.sha256(F.read_bytes()).hexdigest()==H

def test_b2_no_response_parsed():
 x=json.loads(F.read_text());assert x['status']=='HEADER_SCREEN_COMPLETE_NOT_BIOLOGY'
 assert x['animal_response_rows_parsed']==0 and x['not_E5_qualified']
 assert x['substantive_G3_or_G4_pass'] is False

def test_documented_source_schema():
 x=json.loads(F.read_text());a=x['sources'];assert len(a)==3
 assert a['camera']['number_of_columns']==23
 assert a['dog']['number_of_columns']==21
 assert a['grid']['number_of_columns']==12
 assert {'Sample Unit','EcoProvence_number','season','operating_days'}.issubset(a['camera']['header_names'])
 assert {'SampleUnit','Fisher','Ecoregion'}.issubset(a['dog']['header_names'])
 assert not any('time' in t.lower() or 'date' in t.lower() for t in a['dog']['header_names'])
