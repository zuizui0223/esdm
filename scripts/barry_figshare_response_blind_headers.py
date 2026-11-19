#!/usr/bin/env python3
"""B2: verify exact Barry Figshare bytes and inspect CSV header only, no response rows."""
from __future__ import annotations
import argparse, csv, hashlib, io, json
from pathlib import Path

PINNED = {
 'camera':('CamStations_Ecosphere.csv',31117351,211555,'0c9963ee9a52fdf6d05c15ed1d13193c'),
 'dog':('DogTracks_Ecosphere.csv',31117348,951580,'f3ae1ac01ad3b0b48d909a3f86845552'),
 'grid':('WestOR_grid_Ecosphere.csv',31117429,1105856,'ca5b3a850474ce09cf2a75d8c667e898'),
}
FAMILIES={
 'station_or_unit':['site','station','plot','camera','cam','unit','uid','grid','id'],
 'ecoregion':['eco','region','klamath','cascade','ecosection','stratum'],
 'method_or_detector':['camera','cam','dog','method','detector','survey','protocol'],
 'effort_or_time':['date','time','season','year','month','start','end','effort','duration','days','nights','length'],
 'observation_or_presence':['detect','presence','species','fisher','occasion','scat','segment','observed','capture'],
}
def file_digest(path,algo):
 h=hashlib.new(algo)
 with path.open('rb') as stream:
  for part in iter(lambda:stream.read(1048576),b''):h.update(part)
 return h.hexdigest()

def inspect_header(path,pin):
 name,fid,size,md5=pin
 if not path.is_file():raise ValueError('B2_SOURCE_MISSING: '+name)
 if path.stat().st_size!=size:raise ValueError('B2_SOURCE_SIZE_DRIFT: '+name)
 if file_digest(path,'md5')!=md5:raise ValueError('B2_SOURCE_MD5_DRIFT: '+name)
 with path.open('rb') as f: first=f.readline(65537)
 if len(first)>65536 or b'\n' not in first:raise ValueError('B2_HEADER_TOO_LONG_OR_UNTERMINATED')
 line=first.decode('utf-8-sig').strip('\r\n')
 delimiters=',;\t'
 if not any(c in line for c in delimiters):raise ValueError('B2_HEADER_HAS_NO_DELIMITER')
 dialect=csv.Sniffer().sniff(line,delimiters=delimiters)
 cols=next(csv.reader(io.StringIO(line),dialect))
 if len(cols)<2:raise ValueError('B2_TOO_FEW_HEADER_COLUMNS')
 if any(not col.strip() for col in cols):raise ValueError('B2_BLANK_HEADER_COLUMN')
 if len({col.strip().lower() for col in cols})!=len(cols):raise ValueError('B2_DUPLICATE_HEADER_COLUMN')
 if len(cols)>250:raise ValueError('B2_TOO_MANY_HEADER_COLUMNS')
 low=[x.strip().lower() for x in cols]
 concepts={k:[x for x,y in zip(cols,low) if any(t in y for t in ts)] for k,ts in FAMILIES.items()}
 return {'file_id':fid,'name':name,'size_bytes':size,'md5':md5,
         'source_sha256':file_digest(path,'sha256'),
         'number_of_columns':len(cols),'header_names':cols,
         'schema_keyword_matches':concepts,'data_rows_parsed':0}

def run(camera,dog,grid):
 out={'schema_version':1,'contract':'B2_BARRY_HEADER_ONLY_PRE_RESPONSE',
      'source_article_id':16821361,'animal_response_rows_parsed':0,
      'not_E5_qualified':True,'substantive_G3_or_G4_pass':False,'sources':{}}
 try:
  for name,p in {'camera':camera,'dog':dog,'grid':grid}.items():
   out['sources'][name]=inspect_header(p,PINNED[name])
  out['status']='HEADER_SCREEN_COMPLETE_NOT_BIOLOGY'
 except (OSError,ValueError,UnicodeError,csv.Error) as exc:
  out.update({'status':'SOURCE_OR_HEADER_STOP',
              'stop_type':type(exc).__name__,'stop_reason':str(exc)[:220]})
 return out

def main():
 a=argparse.ArgumentParser()
 for x in ('camera','dog','grid','out'):a.add_argument('--'+x,type=Path,required=True)
 x=a.parse_args();x.out.parent.mkdir(parents=True,exist_ok=True)
 result=run(x.camera,x.dog,x.grid)
 x.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'animal_rows':result['animal_response_rows_parsed'],
                   'sources':{k:len(v['header_names']) for k,v in result['sources'].items()}},sort_keys=True))
if __name__=='__main__':main()
