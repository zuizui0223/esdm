#!/usr/bin/env python3
"""Response-blind, deterministic header-only preflight of Snapshot Europe Data S1.

No CSV data row, wildlife label, image, camera ID, taxon value, effect or score
is read. ZIP member names are emitted only for tabular/document schema files.
This is *not* an E5 data qualification, ecological result or source opening.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

MAX_ZIP_BYTES = 250_000_000
MAX_EXPANDED_BYTES = 1_500_000_000
MAX_TABULAR_FILES = 100
MAX_HEADER_BYTES = 32_768
SAFE_EXTENSIONS = {'.csv', '.tsv'}


def digest(path: Path, kind: str = 'sha256') -> str:
    h=hashlib.new(kind)
    with path.open('rb') as stream:
        for blob in iter(lambda: stream.read(1<<20), b''):
            h.update(blob)
    return h.hexdigest()


def tabular_header(raw: bytes, extension: str) -> list[str]:
    if not raw or b'\x00' in raw:
        raise ValueError('HEADER_STOP: missing or binary tabular header')
    try:
        line=raw.decode('utf-8-sig').rstrip('\r\n')
    except UnicodeDecodeError as exc:
        raise ValueError('HEADER_STOP: non-utf8 header') from exc
    if len(line)>MAX_HEADER_BYTES or '\n' in line or '\r' in line:
        raise ValueError('HEADER_STOP: malformed multiline header')
    delim='\t' if extension == '.tsv' else ','
    header = next(csv.reader([line], delimiter=delim), [])
    if not header or any((not col.strip() or len(col)>300) for col in header):
        raise ValueError('HEADER_STOP: invalid blank or huge column')
    return header


def inspect_archive(archive: Path, source_url: str) -> dict:
    size=archive.stat().st_size
    if size>MAX_ZIP_BYTES or size<22:
        raise ValueError('SOURCE_STOP: archive outside predeclared size range')
    if not zipfile.is_zipfile(archive):
        raise ValueError('SOURCE_STOP: source is not a ZIP archive')
    count=Counter()
    tables=[]
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        expanded=sum(i.file_size for i in infos)
        if expanded>MAX_EXPANDED_BYTES or len(infos)>1500:
            raise ValueError('SOURCE_STOP: excessive archive expansion')
        for member in infos:
            if member.is_dir():
                continue
            path=PurePosixPath(member.filename)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('SOURCE_STOP: unsafe archive member path')
            ext=path.suffix.lower()
            count[ext or '<no_extension>'] += 1
            if ext not in SAFE_EXTENSIONS:
                continue
            if len(tables)>=MAX_TABULAR_FILES:
                raise ValueError('SOURCE_STOP: excessive tabular schema files')
            # Read exactly the first physical header line. No record value is parsed.
            with z.open(member) as fh:
                raw=fh.readline(MAX_HEADER_BYTES + 1)
            if len(raw)>MAX_HEADER_BYTES or not raw.endswith((b'\r\n',b'\n')):
                raise ValueError('HEADER_STOP: overlong or unterminated header')
            tables.append({'member':member.filename,'header_columns':tabular_header(raw,ext),
                           'uncompressed_bytes':member.file_size})
    if not tables:
        return {'schema_version':1,'status':'SCHEMA_UNAVAILABLE_NO_CSV_OR_TSV',
                'source_url':source_url,'zip_bytes':size,'zip_sha256':digest(archive),
                'member_extension_counts':dict(sorted(count.items())),
                'tabular_headers':[],'raw_rows_opened':0,'biology_values_opened':False}
    return {'schema_version':1,'status':'RESPONSE_BLIND_HEADER_SCREEN_COMPLETE',
            'source_url':source_url,'zip_bytes':size,'zip_sha256':digest(archive),
            'member_extension_counts':dict(sorted(count.items())),
            'tabular_headers':tables,'raw_rows_opened':0,
            'biology_values_opened':False,
            'e5_g4_detection_calibration_qualified':False,
            'ecological_model_fitted':False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--zip',required=True,type=Path)
    p.add_argument('--source-url',required=True)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    result=inspect_archive(args.zip,args.source_url)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'zip_sha256':result['zip_sha256'],
                      'tabular_file_count':len(result['tabular_headers']),
                      'non_tabular_counts':result['member_extension_counts'],
                      'rows_opened':0},ensure_ascii=False))
if __name__ == '__main__':
    main()
