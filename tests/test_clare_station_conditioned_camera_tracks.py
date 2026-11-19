"""Synthetic-only tests; no Clare animal response is opened here."""
from pathlib import Path
import io,zipfile,csv
import pytest
from scripts import clare_station_conditioned_camera_tracks as m


def encoded(row,header=False,idcol=False):
 buff=io.StringIO(); w=csv.writer(buff)
 if header:w.writerow((['id'] if idcol else [])+[f'Occ{j}' for j in range(1,10)])
 for i in range(238):w.writerow(([str(i+1)] if idcol else [])+list(row))
 return buff.getvalue().encode()


def test_data_unheaded_nine_cols():
 x=m.parse_matrix(encoded([1,2,3,4,None,1,2,3,4]).replace(b',\r\n',b',NA\r\n'))
 assert len(x)==238 and len(x[0])==9 and x[0][0]==1

def test_data_header_and_id():
 x=m.parse_matrix(encoded([1,2,3,4,1,2,3,4,'NA'],header=True,idcol=True))
 assert len(x)==238 and x[0][-1] is None

def test_no_header_but_station_id():
 x=m.parse_matrix(encoded([1,2,3,4,1,2,3,4,1],header=False,idcol=True))
 assert len(x)==238

def test_invalid_code_stops():
 with pytest.raises(ValueError):m.parse_matrix(encoded([0]*9))

def test_wrong_rows_stops():
 buf=io.StringIO();csv.writer(buf).writerow([1]*9)
 with pytest.raises(ValueError,match='238'):m.parse_matrix(buf.getvalue().encode())

def test_study_pair_null_exact_expectation():
 s,c=m.station_stats([[1,2,4,4]+[None]*5])
 assert s[0]['m']==4 and s[0]['c']==1 and s[0]['t']==1
 assert s[0]['expected']==0.25 and s[0]['delta']==-0.25
 assert c['camera_only']==1 and c['tracks_only']==1

def test_synthetic_positive_depends_on_same_occasion():
 x=m.analyze([[3]*4+[4]*5 for _ in range(238)],boot=100)
 assert x['status']=='POSITIVE_WITHIN_STATION_ASSOCIATION'
 assert x['station_bootstrap_95_interval'][0]>0

def test_synthetic_negative_staggered_methods():
 x=m.analyze([[1]*4+[2]*4+[4] for _ in range(238)],boot=100)
 assert x['status']=='NEGATIVE_WITHIN_STATION_ASSOCIATION'
 assert x['station_bootstrap_95_interval'][1]<0

def test_synthetic_null_no_gain():
 x=m.analyze([[3]*9 for _ in range(238)],boot=100)
 assert x['status']=='INCONCLUSIVE_SIGNED_EFFECT'
 assert abs(x['delta_per_observed_paired_occasion'])<1e-12
 assert x['not_E5_G4']

def test_insufficient_support_stop():
 x=m.analyze([[None]*9 for _ in range(238)],boot=10)
 assert x['status']=='INSUFFICIENT_SUPPORT'

def test_bootstrap_seed_deterministic():
 mat=[[1,2,3,4,3,2,1,3,4] for _ in range(238)]
 assert m.analyze(mat,boot=10)==m.analyze(mat,boot=10)

def test_zip_single_expected_path(tmp_path):
 z=tmp_path/'source.zip';d=encoded([1]*9)
 with zipfile.ZipFile(z,'w') as f:f.writestr('nested/MartenOccupancyEncounters.csv',d)
 _,raw=m.load_zip(z);assert raw==d

def test_zip_duplicate_filename_stops(tmp_path):
 z=tmp_path/'source.zip'
 with zipfile.ZipFile(z,'w') as f:
  for name in ['one/MartenOccupancyEncounters.csv','two/MartenOccupancyEncounters.csv']:
   f.writestr(name,encoded([1]*9))
 with pytest.raises(ValueError,match='exactly one'):m.load_zip(z)

def test_zip_non_archive_stops(tmp_path):
 p=tmp_path/'source.zip';p.write_text('HTML PAGE')
 assert m.run(p)['status']=='SOURCE_OR_RESPONSE_SCHEMA_STOP'

def test_zero_outcome_access_when_missing_zip(tmp_path):
 x=m.run(tmp_path/'missing.zip')
 assert x['biological_effect_evaluated'] is False
 assert x['original_E5_qualified_count_unchanged']==0
