#!/usr/bin/env python3
"""Response-blind Barry survey *exposure geometry*; never access camera/dog outcomes."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from collections import defaultdict,Counter

PINNED={
 'camera':('CamStations_Ecosphere.csv',211555,'0c9963ee9a52fdf6d05c15ed1d13193c'),
 'dog':('DogTracks_Ecosphere.csv',951580,'f3ae1ac01ad3b0b48d909a3f86845552')
}
ALLOWED={
 'camera':('Sample Unit','EcoProvence_number','Camera #','season','min_date','max_date','operating_days'),
 'dog':('SampleUnit','EcoProvence_number','SegmentID')
}
PROHIBITED={'Fisher','pepe','caminop','X','Y','East','North','X_Seg','Y_Seg','wild_low','wild_mod','wild_high'}

def digest(p):
 h=hashlib.md5()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()

def rows_allowed_only(path,group):
 name,size,md5=PINNED[group]
 if not path.is_file() or path.stat().st_size!=size or digest(path)!=md5:
  raise ValueError('SOURCE_IDENTITY_STOP_'+group.upper())
 needed=ALLOWED[group]
 if PROHIBITED.intersection(needed):raise ValueError('CONFIGURATION_OUTCOME_LEAK')
 with path.open(encoding='utf-8-sig',newline='') as stream:
  reader=csv.DictReader(stream)
  head=reader.fieldnames or []
  if len(set(head))!=len(head) or not set(needed).issubset(head):
   raise ValueError('REQUIRED_METADATA_HEADER_STOP_'+group.upper())
  for row in reader:
   # Deliberately access ONLY the predeclared non-biological metadata fields.
   yield {k:(row.get(k) or '').strip() for k in needed}

def normalized(value):return ' '.join(str(value).strip().split())

def compute(camera_rows,dog_rows):
 cam=defaultdict(set);dog=defaultdict(set)
 unit_regions_cam=defaultdict(set);unit_regions_dog=defaultdict(set)
 hardware_sites=defaultdict(set)
 cmissing=dmissing=0
 ctotal=dtotal=0
 seasons=Counter();dated=0;effort_count=0
 for r in camera_rows:
  ctotal+=1;eco=normalized(r['EcoProvence_number']);unit=normalized(r['Sample Unit'])
  if not eco or not unit:cmissing+=1;continue
  cam[eco].add(unit);unit_regions_cam[unit].add(eco)
  device=normalized(r['Camera #'])
  if device:hardware_sites[device].add((eco,unit))
  if r['season']:seasons[r['season']]+=1
  if r['min_date'] and r['max_date']:dated+=1
  if r['operating_days']:effort_count+=1
 for r in dog_rows:
  dtotal+=1;eco=normalized(r['EcoProvence_number']);unit=normalized(r['SampleUnit'])
  if not eco or not unit:dmissing+=1;continue
  dog[eco].add(unit);unit_regions_dog[unit].add(eco)
 # Retain no location/animal labels in output; count only publication-defined region categories.
 ecos=sorted(set(cam)|set(dog))
 detail=[]
 for eco in ecos:
  a=cam[eco];b=dog[eco]
  detail.append({'ecoregion_code':eco,'camera_sample_units':len(a),
    'dog_sample_units':len(b),'shared_sample_unit_keys':len(a&b)})
 both=[v for v in detail if v['camera_sample_units']>0 and v['dog_sample_units']>0]
 return {'schema_version':1,'date':'2026-11-19','status':'METADATA_GEOMETRY_EVALUATED_NOT_ECOLOGICAL_EFFECT',
         'scope':'Barry Oregon camera+detection-dog published metadata only',
         'biological_response_fields_accessed':False,'original_E5_qualified_count_unchanged':0,
         'G4_independent_camera_passage_reference_established':False,
         'camera_rows':ctotal,'dog_segment_rows':dtotal,
         'camera_rows_missing_unit_or_region':cmissing,
         'dog_rows_missing_unit_or_region':dmissing,
         'ecoregion_labels_total':len(ecos),'ecoregions_with_both_methods':len(both),
         'ecoregions_with_both_ge10_units':sum(v['camera_sample_units']>=10 and v['dog_sample_units']>=10 for v in detail),
         'ecoregions_with_both_ge10_and_ge3_shared':sum(v['camera_sample_units']>=10 and v['dog_sample_units']>=10 and v['shared_sample_unit_keys']>=3 for v in detail),
         'shared_ecoregion_sample_unit_keys_total':sum(v['shared_sample_unit_keys'] for v in detail),
         'camera_hardware_ids_mapped_to_gt1_unit':sum(len(v)>1 for v in hardware_sites.values()),
         'camera_sample_unit_strings_in_multiple_ecoregions':sum(len(v)>1 for v in unit_regions_cam.values()),
         'dog_sample_unit_strings_in_multiple_ecoregions':sum(len(v)>1 for v in unit_regions_dog.values()),
         'camera_rows_with_declared_min_max_date':dated,
         'camera_rows_with_declared_operating_days':effort_count,
         'camera_distinct_season_labels_count':len(seasons),
         'dog_event_time_available_in_published_header':False,
         'per_ecoregion_sampling_only':detail}

def run(camera:Path,dog:Path):
 try:
  return compute(rows_allowed_only(camera,'camera'),rows_allowed_only(dog,'dog'))
 except (OSError,ValueError,UnicodeError,csv.Error,KeyError) as exc:
  return {'schema_version':1,'status':'METADATA_SOURCE_OR_JOIN_SCHEMA_STOP',
    'stop_type':type(exc).__name__,'stop_reason':str(exc)[:220],
    'biological_response_fields_accessed':False,'original_E5_qualified_count_unchanged':0}

def main():
 p=argparse.ArgumentParser()
 for n in ('camera','dog','out'):p.add_argument('--'+n,required=True,type=Path)
 args=p.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
 r=run(args.camera,args.dog)
 args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
 print(json.dumps({k:r.get(k) for k in ('status','ecoregions_with_both_methods','shared_ecoregion_sample_unit_keys_total')},sort_keys=True))
if __name__=='__main__':main()
