#!/usr/bin/env python3
"""Response-blind public API *metadata* screen for Barry (Figshare) and Clare (Dryad).

Never accesses file download URLs, detection data, animal labels or row values.
Source-specific API access is permitted ONLY for public dataset metadata.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

FIG_URL = 'https://api.figshare.com/v2/articles/16821361'
DRY_URL = 'https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.4mt00'
FIG_DOI = '10.6084/m9.figshare.16821361.v1'
DRY_DOI = '10.5061/dryad.4mt00'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'esdm-response-blind-source-manifest/1.0'}


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def get_json_metadata(url, opener=None):
    """GET only two immutable source metadata URLs; never follow file-member hrefs."""
    if url not in (FIG_URL, DRY_URL):
        raise ValueError('DISALLOWED_SOURCE_URL')
    request = urllib.request.Request(url, headers=HEADERS)
    func = urllib.request.urlopen if opener is None else opener
    with func(request, timeout=35) as stream:
        data = stream.read(6_000_001)
    if len(data) > 6_000_000:
        raise ValueError('METADATA_EXCEEDS_6MB_LIMIT')
    parsed = json.loads(data.decode('utf-8'))
    if not isinstance(parsed, dict):
        raise ValueError('METADATA_JSON_SCHEMA_STOP')
    return parsed, _sha256(data), len(data)


def figshare_manifest(obj):
    if obj.get('id') != 16821361:
        raise ValueError('FIGSHARE_ARTICLE_ID_MISMATCH')
    doi = str(obj.get('doi') or '').strip().lower()
    if doi and doi not in (FIG_DOI.lower(), 'https://doi.org/'+FIG_DOI.lower()):
        # Same article may report its DOI without the v1 version suffix.
        if doi not in ('10.6084/m9.figshare.16821361','https://doi.org/10.6084/m9.figshare.16821361'):
            raise ValueError('FIGSHARE_DOI_MISMATCH')
    raw = obj.get('files')
    if not isinstance(raw,list):
        return {'status':'FILE_LIST_NOT_AVAILABLE','files':[],'file_count':0}
    keep=[]
    for f in raw:
        if not isinstance(f,dict): raise ValueError('FIGSHARE_FILE_SCHEMA_STOP')
        n=f.get('name'); size=f.get('size'); fid=f.get('id')
        if not isinstance(n,str) or not n.strip() or not isinstance(size,int) or size<0 or not isinstance(fid,int):
            raise ValueError('FIGSHARE_FILE_SCHEMA_STOP')
        keep.append({'file_id':fid,'name':n,'size_bytes':size,'checksum_md5':f.get('computed_md5')})
    return {'status':'PUBLIC_MANIFEST_PRESENT','files':keep,'file_count':len(keep), 'doi':FIG_DOI}


def dryad_manifest(obj):
    ids=[str(obj.get(x) or '') for x in ('identifier','doi','id','title')]
    if not any(DRY_DOI in v for v in ids):
        raise ValueError('DRYAD_IDENTITY_NOT_VERIFIED')
    # Dryad /datasets response often contains version & an _links graph rather than files.
    version=obj.get('versionNumber') or obj.get('currentVersion') or obj.get('version')
    files=obj.get('files', None)
    if not isinstance(files,list):
        return {'status':'DATASET_METADATA_PRESENT_FILES_NOT_ENUMERATED','files':[],
                'file_count':None,'version':str(version) if version is not None else None,
                'doi':DRY_DOI,'metadata_keys':sorted(obj.keys())}
    summaries=[]
    for f in files:
        if not isinstance(f,dict):raise ValueError('DRYAD_FILE_SCHEMA_STOP')
        name=f.get('path') or f.get('filename') or f.get('name')
        if name:
            summaries.append({'name':str(name),'size_bytes':f.get('size'),
                              'digest':f.get('digest') or f.get('md5')})
    return {'status':'PUBLIC_MANIFEST_PRESENT','files':summaries,'file_count':len(summaries),
            'version':str(version) if version is not None else None,'doi':DRY_DOI}


def screen_one(name,url,parser,opener=None):
    try:
        obj,hash_value,size=get_json_metadata(url,opener)
        r=parser(obj)
        return {'source':name,'status':r['status'],'public_metadata_url':url,
                'response_rows_opened':0,'original_data_files_downloaded':0,
                'metadata_sha256':hash_value,'metadata_bytes':size,'manifest':r}
    except (ValueError, KeyError, json.JSONDecodeError, urllib.error.HTTPError,
            urllib.error.URLError, TimeoutError, OSError) as e:
        return {'source':name,'status':'METADATA_TRANSPORT_OR_SCHEMA_STOP',
                'public_metadata_url':url,'response_rows_opened':0,
                'original_data_files_downloaded':0,
                'stop_type':type(e).__name__,'stop_reason':str(e)[:300]}


def run(opener=None):
    return {'schema_version':1,'date':'2026-11-19',
            'contract':'B1_RESPONSE_BLIND_PUBLIC_MANIFEST_ONLY',
            'original_E5_qualified_count_unchanged':0,
            'animal_response_opened':False,
            'figshare':screen_one('Barry_figshare',FIG_URL,figshare_manifest,opener),
            'dryad':screen_one('Clare_dryad',DRY_URL,dryad_manifest,opener)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    result=run()
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k]['status'] for k in ('figshare','dryad')},sort_keys=True))

if __name__=='__main__':main()
