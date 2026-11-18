#!/usr/bin/env python3
"""Read ONLY a public Edmond/Dataverse *dataset metadata* API response.

No wildlife records, locations or species data are loaded or modified. This
program accepts JSON bytes already downloaded from the official API.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

PERSISTENT_ID = 'doi:10.17617/3.7YLWMU'
METADATA_URL = 'https://edmond.mpg.de/api/datasets/:persistentId/?persistentId='+PERSISTENT_ID
MAX_MANIFEST_BYTES = 2_000_000
MAX_FILES = 500
MAX_ARCHIVE_BYTES = 250_000_000


def extract_public_manifest(obj: object) -> dict:
    if not isinstance(obj,dict) or str(obj.get('status','')).upper() != 'OK':
        raise ValueError('EDMOND_METADATA_STOP: API response status not OK')
    data=obj.get('data')
    if not isinstance(data,dict) or data.get('persistentId') != PERSISTENT_ID:
        raise ValueError('EDMOND_METADATA_STOP: not the fixed dataset DOI')
    version=data.get('latestVersion')
    if not isinstance(version,dict) or version.get('versionState','RELEASED') not in ('RELEASED','DEACCESSIONED'):
        raise ValueError('EDMOND_METADATA_STOP: no public released version')
    if version.get('versionState')=='DEACCESSIONED':
        raise ValueError('EDMOND_METADATA_STOP: dataset version deaccessioned')
    files=version.get('files')
    if not isinstance(files,list) or not (1 <= len(files) <= MAX_FILES):
        raise ValueError('EDMOND_METADATA_STOP: no bounded published file list')
    out=[]
    for entry in files:
        if not isinstance(entry,dict):
            raise ValueError('EDMOND_METADATA_STOP: invalid file entry')
        f=entry.get('dataFile')
        if not isinstance(f,dict):
            raise ValueError('EDMOND_METADATA_STOP: file missing metadata')
        name=str(entry.get('label') or f.get('filename') or '')
        size=f.get('filesize')
        identifier=f.get('id')
        if not name or '/' in name or '\\' in name or not isinstance(size,int) or size < 0 or not isinstance(identifier,int):
            raise ValueError('EDMOND_METADATA_STOP: invalid file name/size/id')
        checksum=f.get('checksum') or {}
        ck_type=checksum.get('type') if isinstance(checksum,dict) else None
        ck_value=checksum.get('value') if isinstance(checksum,dict) else None
        if ck_value and not re.fullmatch(r'[0-9a-fA-F]{32,128}',str(ck_value)):
            raise ValueError('EDMOND_METADATA_STOP: malformed checksum')
        out.append({'filename':name,'size':size,'file_id':identifier,
                    'restricted':bool(entry.get('restricted') or f.get('restricted')),
                    'checksum_type':ck_type,'checksum':ck_value})
    allowed=[x for x in out if x['filename'].lower().endswith('.zip')
             and not x['restricted'] and 22<=x['size']<=MAX_ARCHIVE_BYTES]
    out.sort(key=lambda x:x['filename'])
    return {'schema_version':1,'status':'EDMOND_PUBLIC_METADATA_READ_NO_RESPONSE',
            'api_url':METADATA_URL,'dataset_doi':PERSISTENT_ID,
            'version':str(version.get('versionNumber'))+'.'+str(version.get('versionMinorNumber',0)),
            'published_file_count':len(out),'files':out,
            'eligible_zip_file_ids':[x['file_id'] for x in allowed],
            'single_unrestricted_zip':len(allowed)==1,
            'source_rows_opened':0,'animal_data_read':False,
            'ecological_fit_performed':False,'E5_G4_pass':False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--json',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--file-id-out',type=Path,required=True)
    args=p.parse_args()
    raw=args.json.read_bytes()
    if len(raw)>MAX_MANIFEST_BYTES:
        raise ValueError('EDMOND_METADATA_STOP: excessive metadata response')
    obj=json.loads(raw)
    result=extract_public_manifest(obj)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    args.file_id_out.parent.mkdir(parents=True,exist_ok=True)
    if result['single_unrestricted_zip']:
        args.file_id_out.write_text(str(result['eligible_zip_file_ids'][0]),encoding='ascii')
    else:
        args.file_id_out.write_text('',encoding='ascii')
    print(json.dumps({'status':result['status'],'version':result['version'],
                      'file_count':result['published_file_count'],
                      'single_unrestricted_zip':result['single_unrestricted_zip']}))
if __name__=='__main__':main()
