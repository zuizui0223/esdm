"""Read-only GBIF download DOI poll for already-accepted NeoBat download keys.

This script NEVER submits or retries a download request. It only GETs
public status metadata using the recorded GBIF download key.
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

KEY_PATTERN = re.compile(r"^[A-Za-z0-9-]{10,80}$")
DOI_PATTERN = re.compile(r"^(?:https?://doi\.org/)?10\.15468/dl\.[a-z0-9]+$",re.I)
GROUPS = ("bat","plant")

def clean_doi(x):
    if not isinstance(x,str):
        return None
    doi=x.strip().removeprefix("doi:")
    return doi if DOI_PATTERN.fullmatch(doi) else None

def inspect_key(key, http_get=None):
    if not isinstance(key,str) or not KEY_PATTERN.fullmatch(key):
        raise ValueError("INVALID_GBIF_DOWNLOAD_KEY")
    if http_get is None:
        def http_get(url):
            req=Request(url,headers={"User-Agent":"esdm-NeoBat-readonly-DOI-poll/1.0",
                                     "Accept":"application/json"})
            with urlopen(req,timeout=45) as resp:
                return json.loads(resp.read().decode())
    try:
        item=http_get("https://api.gbif.org/v1/occurrence/download/"+key)
    except HTTPError as exc:
        return {"status":"POLL_HTTP_STOP","http_code":exc.code,"download_key":key}
    except (OSError,URLError,ValueError) as exc:
        return {"status":"POLL_TRANSPORT_STOP","exception_type":type(exc).__name__,"download_key":key}
    if not isinstance(item,dict) or item.get("key") not in (key,None):
        return {"status":"POLL_SCHEMA_STOP","download_key":key}
    state=item.get("status")
    if state not in ("PREPARING","RUNNING","SUCCEEDED","KILLED","CANCELLED","SUSPENDED","FAILED"):
        return {"status":"POLL_UNKNOWN_STATUS","reported_status":str(state)[:70],"download_key":key}
    doi=clean_doi(item.get("doi"))
    return {"status":state,"download_key":key,"doi":doi,
            "GBIF_total_records":item.get("totalRecords"),
            "GBIF_number_datasets":item.get("numberDatasets"),
            "GBIF_size_bytes":item.get("size"),
            "metadata_modified":item.get("modified"),
            "download_link":(item.get("downloadLink") if state=="SUCCEEDED" and doi else None),
            "eligible_for_next_full_source_verification":state=="SUCCEEDED" and doi is not None}

def poll_receipt(src, *, http_get=None):
    if src.get("status") not in ("BOTH_DOWNLOADS_REQUESTED","PARTIAL_SUBMISSION_STOP"):
        raise ValueError("NO_ACCEPTED_SUBMISSIONS_RECORDED")
    keys=src.get("download_keys")
    if not isinstance(keys,dict) or not keys:
        raise ValueError("NO_DOWNLOAD_KEYS")
    out={"schema_version":1,"status":"POLL_ONLY",
         "checked_at_utc":datetime.now(timezone.utc).isoformat(),
         "submitted_source_status":src["status"],
         "source_submission_created_at":src.get("created_utc"),
         "no_new_download_requests":True,
         "ecological_result":None,
         "downloads":{}}
    for group in GROUPS:
        key=keys.get(group)
        out["downloads"][group]=inspect_key(key,http_get) if key else {
            "status":"NEVER_SUBMITTED","download_key":None}
    if all(out["downloads"][g].get("eligible_for_next_full_source_verification") for g in GROUPS):
        out["status"]="BOTH_DOIS_VERIFIED_BY_PUBLIC_GBIF_METADATA"
    elif any(x["status"].endswith("STOP") or x["status"]=="POLL_UNKNOWN_STATUS"
             for x in out["downloads"].values()):
        out["status"]="POLL_INCOMPLETE"
    return out

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--input",default="docs/replication/neobat/gbif_download_submission.json")
    pa.add_argument("--out",default="build/neobat/gbif_download_doi_poll.json")
    args=pa.parse_args()
    dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        data=json.loads(pathlib.Path(args.input).read_text())
        out=poll_receipt(data)
    except Exception as exc:
        out={"schema_version":1,"status":"NO_VALID_SUBMISSION_RECEIPT",
             "error_code":type(exc).__name__+":"+str(exc)[:100],
             "new_download_requests":0,"ecological_result":None}
    dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("GBIF_DOI_POLL:",out["status"],"groups=",
          {k:v["status"] for k,v in out.get("downloads",{}).items()},flush=True)
    return 0 if out["status"] not in ("NO_VALID_SUBMISSION_RECEIPT","POLL_INCOMPLETE") else 3

if __name__=="__main__":
    sys.exit(main())
