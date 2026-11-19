"""Submit two DOI-bearing GBIF occurrence downloads for the frozen NeoBat cohort.

Uses GitHub Actions secrets ONLY in process memory. No raw credentials or
email in the saved receipt. One-shot trigger is a separate immutable marker.
Predicates use the old GBIF Backbone key namespace, matching /species/match
without checklistKey. Never silently switch to Catalogue of Life keys.
"""
from __future__ import annotations
import argparse, base64, copy, hashlib, json, os, pathlib, re, sys, time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PINNED_TEMPLATE_BLOB = "8719955456e238f30efb652edaadf1ae2347daa1"
PINNED_BAT_META_BLOB = "200837896033fdb06276486480d30b0042418432"
PINNED_PLANT_META_BLOB = "7c810fea62fd6e0e4bbe215faccad6900e858055"
GROUPS = {"bat":26,"plant":255}
COUNTRIES = 29
BASENAME = "docs/replication/neobat/gbif_bulk_download_request_drafts.json"
BATPATH = "docs/replication/neobat/gbif_search_preflight.json"
PLANTPATH = "docs/replication/neobat/plant_search_preflight.json"
BASE = "https://api.gbif.org/v1/occurrence/download"

def blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def load_exact(path, expected):
    data = pathlib.Path(path).read_bytes()
    if blob_sha(data)!=expected:
        raise RuntimeError("PINNED_INPUT_BLOB_MISMATCH:"+str(path))
    return json.loads(data), hashlib.sha256(data).hexdigest()

def prepare(draft,bat,plant,username,email):
    if draft.get("status")!="DRAFT_NOT_DISPATCHED":
        raise RuntimeError("REQUEST_TEMPLATE_STATUS_STOP")
    if not username or not email or "@" not in email:
        raise RuntimeError("CREDENTIAL_FIELDS_EMPTY")
    batrows = [x for x in bat.get("records",[]) if x.get("status") in
               ("GBIF_COUNTS_ONLY","GBIF_COUNTS_AUDITED_ALIAS")]
    plantrows = [x for x in plant.get("plants",[]) if x.get("status")=="GBIF_PLANT_COUNTS_ONLY"]
    lookup={"bat":batrows,"plant":plantrows}
    requests={}
    for group,expected_n in GROUPS.items():
        roster=lookup[group]
        if len(roster)!=expected_n:
            raise RuntimeError("TAXON_DENOMINATOR_CHANGED:"+group)
        actual_keys={str(x["match"].get("acceptedUsageKey") or x["match"]["usageKey"])
                     for x in roster}
        if len(actual_keys)!=expected_n:
            raise RuntimeError("ACCEPTED_TAXON_KEY_DUPLICATION:"+group)
        r=draft["download_request_templates"][group]
        if r.get("format")!="SIMPLE_CSV" or r.get("predicate",{}).get("type")!="and":
            raise RuntimeError("BAD_DOWNLOAD_FORMAT_OR_PREDICATE:"+group)
        predicates=r["predicate"]["predicates"]
        found={(p["type"],p.get("key")):p for p in predicates}
        key_pred=found.get(("in","TAXON_KEY"))
        cc_pred=found.get(("in","COUNTRY"))
        if not key_pred or not cc_pred:
            raise RuntimeError("MISSING_GROUP_OR_COUNTRY_PREDICATE:"+group)
        requested_keys={str(x) for x in key_pred.get("values",[])}
        if requested_keys!=actual_keys or len(key_pred["values"])!=expected_n:
            raise RuntimeError("TAXON_KEY_MISMATCH:"+group)
        if len(cc_pred.get("values",[]))!=COUNTRIES:
            raise RuntimeError("COUNTRY_DENOMINATOR_MISMATCH:"+group)
        expected={
            ("equals","HAS_COORDINATE"):"true",
            ("equals","HAS_GEOSPATIAL_ISSUE"):"false",
            ("equals","OCCURRENCE_STATUS"):"PRESENT",
            ("greaterThanOrEquals","YEAR"):"2000",
            ("lessThanOrEquals","YEAR"):"2025",
        }
        for k,v in expected.items():
            if str(found.get(k,{}).get("value","")).lower()!=v.lower():
                raise RuntimeError("MISSING_OR_CHANGED_FILTER:"+group+":"+str(k))
        if len(predicates)!=7 or "checklistKey" in r:
            raise RuntimeError("PREDICATE_UNIVERSE_OR_CHECKLIST_CHANGED:"+group)
        for pp in predicates:
            if pp.get("checklistKey"):
                raise RuntimeError("MIXED_TAXONOMY_NAMESPACE_STOP")
        req=copy.deepcopy(r)
        req.update(
            creator=username,
            notificationAddresses=[email],
            sendNotification=False,
            description=("esdm NeoBat resource SDM prefit, "+group+
                         ", frozen author-source 26 bat/255 plant cohort, "+
                         "Neotropical country proxy 2000-2025, GBIF Backbone keys")
        )
        # Deliberately omit checklistKey: source species/match keys came from
        # the default, legacy GBIF Backbone taxonomy.
        requests[group]=req
    return requests

def perform(url, *, method="GET", data=None, headers=None):
    request=Request(url,data=data,method=method,headers=headers or {
        "Accept":"application/json",
        "User-Agent":"esdm-NeoBat-DOI-submission/1.0"
    })
    try:
        with urlopen(request,timeout=60) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as exc:
        # Do not read, print or persist server body; it may echo username/email.
        raise RuntimeError("GBIF_HTTP_"+str(exc.code)) from None
    except (URLError,OSError,TimeoutError) as exc:
        raise RuntimeError("GBIF_TRANSPORT_"+type(exc).__name__) from None

def submit(request,username,password):
    credential=base64.b64encode((username+":"+password).encode()).decode()
    body=json.dumps(request,separators=(",",":")).encode()
    response=perform(BASE+"/request",method="POST",data=body,
                     headers={"Authorization":"Basic "+credential,
                              "Content-Type":"application/json",
                              "Accept":"text/plain, application/json",
                              "User-Agent":"esdm-NeoBat-DOI-submission/1.0"})
    key=response.strip().strip('"')
    if not re.fullmatch(r"[A-Za-z0-9-]{10,80}",key):
        raise RuntimeError("GBIF_UNEXPECTED_DOWNLOAD_KEY_FORMAT")
    return key,hashlib.sha256(body).hexdigest()

def read_status(key):
    response=perform(BASE+"/"+key)
    try:
        meta=json.loads(response)
    except (json.JSONDecodeError,ValueError):
        raise RuntimeError("DOWNLOAD_STATUS_SCHEMA_STOP") from None
    return {name:meta.get(name) for name in (
        "key","status","doi","downloadLink","created","modified",
        "totalRecords","size","numberDatasets")}

def save(out,receipt):
    pathlib.Path(out).parent.mkdir(parents=True,exist_ok=True)
    pathlib.Path(out).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="build/neobat/gbif_download_submission.json")
    args=parser.parse_args()
    user=os.environ.get("GBIF_USERNAME") or os.environ.get("GBIF_USERNAME_VAR")
    password=os.environ.get("GBIF_PASSWORD")
    email=os.environ.get("GBIF_EMAIL")
    receipt={
        "schema_version":1,
        "status":"NOT_SUBMITTED",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source":"GBIF occurrence/download/request",
        "taxonomy_namespace":"legacy GBIF Backbone (default for species/match and download)",
        "DOI_downloads_requested":[],
        "download_keys":{},
        "request_sha256":{},
        "download_metadata":{},
        "credentials_or_email_saved":False,
        "ecological_result":None
    }
    try:
        if not user or not password or not email:
            raise RuntimeError("AUTH_CONFIG_INCOMPLETE")
        draft,digest=load_exact(BASENAME,PINNED_TEMPLATE_BLOB)
        bat,bat_hash=load_exact(BATPATH,PINNED_BAT_META_BLOB)
        plant,plant_hash=load_exact(PLANTPATH,PINNED_PLANT_META_BLOB)
        receipt["frozen_source_sha256"]={"request_template":digest,
                                        "bat_name":bat_hash,"plant_name":plant_hash}
        requests=prepare(draft,bat,plant,user,email)
        receipt["status"]="SUBMITTING"
        save(args.out,receipt)
        for group in GROUPS:
            key,predigest=submit(requests[group],user,password)
            receipt["download_keys"][group]=key
            receipt["request_sha256"][group]=predigest
            receipt["DOI_downloads_requested"].append(group)
            receipt["download_metadata"][group]=read_status(key)
            save(args.out,receipt)
            print("GBIF_SUBMISSION_ACCEPTED",group,key,flush=True)
        receipt["status"]="BOTH_DOWNLOADS_REQUESTED"
    except Exception as exc:
        receipt["status"]="SUBMISSION_STOP" if not receipt["download_keys"] else "PARTIAL_SUBMISSION_STOP"
        receipt["error_code"]=str(exc)[:160]
    save(args.out,receipt)
    print("GBIF_REQUEST_GATE:",receipt["status"],
          "groups=",list(receipt["download_keys"]),flush=True)
    return 0 if receipt["status"]=="BOTH_DOWNLOADS_REQUESTED" else 3

if __name__=="__main__":
    sys.exit(main())
