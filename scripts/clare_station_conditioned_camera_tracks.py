#!/usr/bin/env python3
"""One-shot exact station-margin co-detection analysis: Clare 2017 Maine martens.

Source response opened only after pre-response design freeze. No animal/site records exported.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,random,zipfile
from pathlib import Path

DATASET_DOI='10.5061/dryad.4mt00'
TARGET='MartenOccupancyEncounters.csv'
N_STATIONS=238
N_OCCASIONS=9
N_BOOT=2000
SEED=20261119
MISSING={'','NA','NaN','NAN','nan','N/A'}


def sha(data):return hashlib.sha256(data).hexdigest()

def normalize_row(raw,width):
 if len(raw)!=width:raise ValueError('RESPONSE_SCHEMA_STOP: inconsistent CSV width')
 return [x.strip() for x in raw]

def coded(v):
 s=v.strip()
 if s in MISSING:return None
 if s not in ('1','2','3','4'):
  raise ValueError('RESPONSE_SCHEMA_STOP: unsupported detection code')
 return int(s)

def parse_matrix(blob):
 try:text=blob.decode('utf-8-sig')
 except UnicodeError as e:raise ValueError('RESPONSE_SCHEMA_STOP: unsupported encoding') from e
 rows=list(csv.reader(io.StringIO(text)))
 rows=[r for r in rows if any(x.strip() for x in r)]
 if not rows:raise ValueError('RESPONSE_SCHEMA_STOP: empty file')
 width=len(rows[0])
 if width not in (N_OCCASIONS,N_OCCASIONS+1):
  raise ValueError('RESPONSE_SCHEMA_STOP: expected 9 (+optional station id) columns')
 # A first row containing non-code occasion labels is a header, never an observed occasion.
 body_start=0
 check=rows[0][1:] if width==10 else rows[0]
 if any(x.strip() not in MISSING|{'1','2','3','4'} for x in check):body_start=1
 body=rows[body_start:]
 if len(body)!=N_STATIONS:
  raise ValueError('RESPONSE_SCHEMA_STOP: 238 station rows required')
 seen=set();out=[]
 for ix,raw in enumerate(body):
  row=normalize_row(raw,width)
  if width==10:
   sid=row[0]
   if not sid or sid in seen:raise ValueError('RESPONSE_SCHEMA_STOP: blank/duplicate station ID')
   seen.add(sid)
   data=row[1:]
  else:data=row
  out.append([coded(x) for x in data])
 return out

def load_zip(path):
 if not path.is_file():raise ValueError('TRANSPORT_OR_SOURCE_STOP: missing ZIP')
 raw=path.read_bytes()
 if not zipfile.is_zipfile(io.BytesIO(raw)):
  raise ValueError('TRANSPORT_OR_SOURCE_STOP: non-ZIP download')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  paths=[name for name in z.namelist() if name.rsplit('/',1)[-1]==TARGET and not name.endswith('/')]
  if len(paths)!=1:raise ValueError('SOURCE_SCHEMA_STOP: expected exactly one marten encounter file')
  if z.getinfo(paths[0]).file_size>1000000:raise ValueError('SOURCE_SCHEMA_STOP: encounter file unexpectedly large')
  source=z.read(paths[0])
 return raw,source

def station_stats(matrix):
 out=[];counts={'camera_only':0,'tracks_only':0,'both':0,'neither':0,'missing':0}
 for row in matrix:
  observed=[v for v in row if v is not None]
  for v in row:
   counts[{None:'missing',1:'camera_only',2:'tracks_only',3:'both',4:'neither'}[v]]+=1
  m=len(observed);c=sum(v in (1,3) for v in observed);t=sum(v in (2,3) for v in observed);b=sum(v==3 for v in observed)
  expected=c*t/m if m else 0.0
  out.append({'m':m,'c':c,'t':t,'b':b,'expected':expected,'delta':b-expected})
 return out,counts

def _percentile(sorted_x,p):
 if not sorted_x:return None
 pos=p*(len(sorted_x)-1);lo=int(pos);hi=min(lo+1,len(sorted_x)-1)
 return sorted_x[lo]+(pos-lo)*(sorted_x[hi]-sorted_x[lo])

def analyze(matrix,seed=SEED,boot=N_BOOT):
 if len(matrix)!=N_STATIONS or any(len(r)!=N_OCCASIONS for r in matrix):
  raise ValueError('RESPONSE_SCHEMA_STOP: source station×occasion dimensions')
 stats,counts=station_stats(matrix)
 n=sum(s['m'] for s in stats);cp=sum(s['c'] for s in stats);tp=sum(s['t'] for s in stats)
 support={'stations':len(matrix),'stations_with_2plus_observations':sum(s['m']>=2 for s in stats),
  'observed_paired_occasions':n,'camera_detection_occasions':cp,'snow_track_detection_occasions':tp}
 if support['stations_with_2plus_observations']<150 or n<500 or cp<25 or tp<25:
  return {'status':'INSUFFICIENT_SUPPORT','support':support,'counts':counts}
 observed_both=sum(s['b'] for s in stats);expected_both=sum(s['expected'] for s in stats)
 delta=(observed_both-expected_both)/n
 rng=random.Random(seed);boots=[]
 for _ in range(boot):
  idx=[rng.randrange(N_STATIONS) for _ in range(N_STATIONS)]
  denom=sum(stats[i]['m'] for i in idx)
  boots.append(sum(stats[i]['delta'] for i in idx)/denom if denom else 0.0)
 boots.sort();low=_percentile(boots,0.025);high=_percentile(boots,0.975)
 positive=delta>=0.02 and low>0
 negative=delta<=-0.02 and high<0
 return {'status':'POSITIVE_WITHIN_STATION_ASSOCIATION' if positive else 'NEGATIVE_WITHIN_STATION_ASSOCIATION' if negative else 'INCONCLUSIVE_SIGNED_EFFECT',
  'support':support,'counts':counts,'observed_both':observed_both,'station_margin_null_expected_both':expected_both,
  'delta_per_observed_paired_occasion':delta,'station_bootstrap_95_interval':[low,high],
  'bootstrap_n':boot,'bootstrap_seed':seed,'not_detection_calibrated':True,
  'not_true_occupancy_or_multiregion_transfer':True,'not_E5_G4':True}

def run(path):
 try:
  raw,source=load_zip(path)
  matrix=parse_matrix(source)
  result=analyze(matrix)
  result.update({'schema_version':1,'date':'2026-11-19','source':{'doi':DATASET_DOI,'version':1,
                   'download_package_sha256':sha(raw),'target_file_sha256':sha(source),
                   'target_file_bytes':len(source)},
                 'original_E5_qualified_count_unchanged':0,
                 'individual_station_or_species_records_exported':False})
  return result
 except (ValueError,OSError,zipfile.BadZipFile,csv.Error) as e:
  return {'schema_version':1,'status':'SOURCE_OR_RESPONSE_SCHEMA_STOP',
          'reason':str(e)[:250],'type':type(e).__name__,
          'original_E5_qualified_count_unchanged':0,'biological_effect_evaluated':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
 res=run(args.zip)
 args.out.write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':res['status'],'delta':res.get('delta_per_observed_paired_occasion'),
                   'support':res.get('support')},sort_keys=True))
if __name__=='__main__':main()
