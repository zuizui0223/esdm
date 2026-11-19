"""Source-only GBIF ZIP acquisition and archive/header audit.

Requires TWO successful public download metadata receipts and the original
pinned accepted download keys. Never opens biological rows for modelling;
only SHA256, ZIP structure, headers, DOI, and GBIF metadata are retained.
"""
from __future__ import annotations
import argparse, hashlib, io, json, pathlib, re, sys, zipfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_ZIP_BYTES=1_500_000_000
MAX_ENTRIES=25
CRITICAL={"gbifid","datasetkey","countrycode","decimallatitude","decimallongitude"}
TAXON_OPTIONS={"taxonkey","specieskey"}
GBIF_DOI=re.compile(r"^(?:https?://doi\.org/)?10\.15468/dl\.[a-z0-9]+$",re.I)
KEY_RE=re.compile(r"^[A-Za-z0-9-]{10,80}$")
GROUPS=("bat","plant")

def verified_source(submission, poll):
    if submission.get("status")!="BOTH_DOWNLOADS_REQUESTED":
        raise RuntimeError("NO_TWO_ACCEPTED_DOWNLOAD_REQUESTS")
    if poll.get("status")!="BOTH_DOIS_VERIFIED_BY_PUBLIC_GBIF_METADATA":
        raise RuntimeError("GBIF_DOIS_NOT_YET_VERIFIED")
    out={}
    for group in GROUPS:
        key=submission.get("download_keys",{}).get(group)
        item=poll.get("downloads",{}).get(group) or {}
        doi=item.get("doi")
        if not isinstance(key,str) or not KEY_RE.fullmatch(key):
            raise RuntimeError("DOWNLOAD_KEY_MISSING_OR_INVALID:"+group)
        if item.get("download_key")!=key:
            raise RuntimeError("POLL_KEY_DOES_NOT_MATCH_SUBMISSION:"+group)
        if item.get("status")!="SUCCEEDED" or not isinstance(doi,str) or not GBIF_DOI.fullmatch(doi):
            raise RuntimeError("PUBLIC_DOI_NOT_VALID:"+group)
        url=item.get("download_link")
        if not isinstance(url,str):
            raise RuntimeError("ARCHIVE_LINK_MISSING:"+group)
        parsed=urlparse(url)
        if parsed.scheme!="https" or parsed.hostname!="api.gbif.org" or (
                "/v1/occurrence/download/request/"+key+".zip" not in parsed.path):
            raise RuntimeError("ARCHIVE_SOURCE_NOT_GBIF_API:"+group)
        out[group]={"download_key":key,"doi":doi,"url":url,
                    "metadata_record_count":item.get("GBIF_total_records")}
    return out

def safe_archive(url,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        raise RuntimeError("OUTPUT_EXISTS_NO_SILENT_OVERWRITE")
    h=hashlib.sha256();size=0
    req=Request(url,headers={"User-Agent":"esdm-NeoBat-DOI-source-only-preflight"})
    try:
        with urlopen(req,timeout=160) as r, target.open("xb") as out:
            while True:
                block=r.read(1024*1024)
                if not block: break
                size+=len(block)
                if size>MAX_ZIP_BYTES: raise RuntimeError("ARCHIVE_SIZE_GATE_STOP")
                h.update(block);out.write(block)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return {"sha256":h.hexdigest(),"zip_size_bytes":size}

def inspect_zip(path):
    if not zipfile.is_zipfile(path):
        raise RuntimeError("NOT_A_ZIP_ARCHIVE")
    with zipfile.ZipFile(path) as z:
        names=z.infolist()
        if len(names)>MAX_ENTRIES:
            raise RuntimeError("TOO_MANY_ZIP_ENTRIES")
        if any(m.filename.startswith("/") or ".." in pathlib.PurePosixPath(m.filename).parts
               for m in names):
            raise RuntimeError("UNSAFE_ZIP_ENTRY")
        candidates=[m for m in names if not m.is_dir() and m.filename.lower().endswith((".csv",".tsv",".txt"))
                    and m.file_size>100 and not m.filename.lower().endswith(("citation.txt","readme.txt"))]
        if len(candidates)!=1:
            raise RuntimeError("EXPECTED_ONE_PRIMARY_SIMPLE_CSV_FILE")
        member=candidates[0]
        if member.file_size>8_000_000_000:
            raise RuntimeError("UNCOMPRESSED_ARCHIVE_SIZE_STOP")
        with z.open(member) as f:
            header_bytes=f.readline(131072)
        try:header=header_bytes.decode("utf-8-sig").strip("\r\n")
        except UnicodeDecodeError:
            header=header_bytes.decode("latin-1").strip("\r\n")
        if "\t" not in header:
            raise RuntimeError("EXPECTED_TSV_HEADER")
        cols=[v.strip() for v in header.split("\t")]
        fields={v.lower() for v in cols}
        if not CRITICAL.issubset(fields):
            raise RuntimeError("MISSING_CRITICAL_GBIF_COLUMNS")
        if not fields.intersection(TAXON_OPTIONS):
            raise RuntimeError("MISSING_GBIF_TAXON_COLUMN")
        return {"zip_entry_name":member.filename,"entry_compressed_size":member.compress_size,
                "entry_uncompressed_size":member.file_size,
                "header_columns":cols,
                "critical_columns_present":True,
                "coordinate_uncertainty_column_present":"coordinateuncertaintyinmeters" in fields,
                "not_a_response_row_opening":True}

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--submission",default="docs/replication/neobat/gbif_download_submission.json")
    pa.add_argument("--poll",default="docs/replication/neobat/gbif_download_doi_poll.json")
    pa.add_argument("--out",default="build/neobat/gbif_archive_header_preflight.json")
    pa.add_argument("--archive-dir",default="build/neobat/original_downloads")
    args=pa.parse_args()
    output=pathlib.Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    receipt={"schema_version":1,"status":"ARCHIVE_NOT_STARTED","files":{},
             "source_only":True,"ecological_effect":None,
             "GBIF_downloads_resubmitted":False}
    try:
        raw_sub=pathlib.Path(args.submission).read_bytes()
        raw_poll=pathlib.Path(args.poll).read_bytes()
        origin=verified_source(json.loads(raw_sub),json.loads(raw_poll))
        receipt["input_sha256"]={
            "submission_receipt":hashlib.sha256(raw_sub).hexdigest(),
            "doi_poll_receipt":hashlib.sha256(raw_poll).hexdigest()
        }
        for group in GROUPS:
            meta=origin[group]
            target=pathlib.Path(args.archive_dir)/(group+"_"+meta["download_key"]+".zip")
            dig=safe_archive(meta["url"],target)
            entry=inspect_zip(target)
            receipt["files"][group]={
                "download_key":meta["download_key"],
                "doi":meta["doi"],
                "source_gbif_record_count":meta["metadata_record_count"],
                **dig,**entry
            }
            output.write_text(json.dumps(receipt,indent=2)+"\n")
            print("ARCHIVE_SOURCE_VERIFIED",group,dig["sha256"],flush=True)
        receipt["status"]="BOTH_ARCHIVE_HEADERS_VERIFIED"
    except Exception as exc:
        receipt["status"]="SOURCE_ARCHIVE_PREFLIGHT_STOP"
        receipt["error_type"]=type(exc).__name__
        receipt["error_code"]=str(exc)[:180]
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print("GBIF_ARCHIVE_PREFLIGHT",receipt["status"],flush=True)
    return 0 if receipt["status"]=="BOTH_ARCHIVE_HEADERS_VERIFIED" else 3

if __name__=="__main__":
    sys.exit(main())
