"""Source-only WorldClim ZIP member SHA forensic, not an ecological fit.

Diagnoses original archive SHA vs internally pinned member SHA. Never
silently changes original scientific source, uses no bat/plant occurrences.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, zipfile
from datetime import datetime, timezone
from scripts import neobat_worldclim_source_preflight as w

def inspect_members(path):
    archive_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    if archive_hash!=w.ARCHIVE_SHA256:
        raise ValueError("FROZEN_WORLDCLIM_ARCHIVE_SHA_STOP")
    result={}
    with zipfile.ZipFile(path) as z:
        for variable,member in w.RASTERS.items():
            if z.namelist().count(member)!=1:
                raise ValueError("WORLDCLIM_MISSING_OR_DUPLICATE_MEMBER_"+variable)
            h=hashlib.sha256()
            total=0
            with z.open(member) as stream:
                while True:
                    chunk=stream.read(1<<20)
                    if not chunk:break
                    h.update(chunk);total+=len(chunk)
            observed=h.hexdigest()
            expected=w.BIO12_SHA256 if variable=="BIO12" else None
            result[variable]={
                "member_name":member,
                "observed_sha256":observed,
                "uncompressed_bytes":total,
                "previously_pinned_sha256":expected,
                "matches_previous_pin":None if expected is None else observed==expected,
                "source_version":"WorldClim v2.1, 10 arc-minute, 1970-2000"}
    return {
        "status":"INNER_MEMBER_HASH_DIAGNOSTIC_ONLY",
        "archive_sha256":archive_hash,
        "archive_sha_matches_fixed_reference":True,
        "source_url":w.SOURCE_URL,
        "no_ecological_responses_opened":True,
        "no_raster_values_extracted":True,
        "no_SDM_fit":True,
        "not_a_replacement_preflight":True,
        "members":result
    }

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--out",default="docs/replication/neobat/worldclim_member_hash_diagnostic.json")
    args=pa.parse_args()
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/"source.zip"
            sha,bytes_count=w.checksum_download(w.SOURCE_URL,p)
            receipt=inspect_members(p)
            receipt["downloaded_archive_sha256"]=sha
            receipt["downloaded_archive_bytes"]=bytes_count
    except Exception as exc:
        receipt={"status":"HASH_FORENSIC_SOURCE_STOP",
                 "error_type":type(exc).__name__,
                 "error_code":str(exc)[:160],
                 "no_ecological_responses_opened":True}
    receipt["checked_utc"]=datetime.now(timezone.utc).isoformat()
    out.write_text(json.dumps(receipt,indent=2)+"\n")
    print("WORLDCLIM_MEMBER_HASH_FORENSIC",receipt["status"],flush=True)
    return 0 if receipt["status"]=="INNER_MEMBER_HASH_DIAGNOSTIC_ONLY" else 3

if __name__=="__main__":
    raise SystemExit(main())
