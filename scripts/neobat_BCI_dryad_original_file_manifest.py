"""NeoBat independent BCI 2026 tree plot: public Dryad API metadata only.

Source/Dryad version/file inventory first; NO original tree observations,
species, plot coordinates, source ZIP bytes, GBIF or bat data are downloaded.
Reject link redirects off the official host or outside /api/v2/.
"""
from __future__ import annotations
import argparse
import json
import pathlib
from datetime import datetime,timezone
from urllib.parse import urljoin,urlparse
from urllib.request import Request,urlopen

API_BASE="https://datadryad.org"
DOI="doi:10.5061/dryad.1g1jwsvc3"
ENTRY="https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.1g1jwsvc3"
DESIGN="docs/replication/NEOBAT_BCI_DRYAD_EXTERNAL_PLOT_API_MANIFEST_FROZEN_20261119.md"
MAX_JSON_BYTES=2_000_000
MAX_PAGES=10
SOURCE_PASS="EXTERNAL_BCI_DRYAD_AUTHOR_VERSION_AND_FILE_METADATA_VERIFIED"


def exact_api_url(href):
    if not isinstance(href,str) or not href:
        raise ValueError("DRYAD_METADATA_LINK_MISSING")
    url=urljoin(API_BASE,href)
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!="datadryad.org" or \
       not parsed.path.startswith("/api/v2/") or \
       parsed.username is not None or parsed.password is not None:
        raise ValueError("DRYAD_API_LINK_OFF_OFFICIAL_HOST_OR_ENDPOINT")
    return url


def get_json(url):
    target=exact_api_url(url)
    req=Request(target,headers={
        "Accept":"application/json",
        "User-Agent":"esdm-NeoBat-BCI-metadata-only-source-audit/1.0"
    })
    with urlopen(req,timeout=40) as response:
        final=exact_api_url(response.url)
        if final!=target:
            raise RuntimeError("DRYAD_PUBLIC_METADATA_REDIRECT_CHANGED")
        if response.status!=200:
            raise RuntimeError("DRYAD_META_HTTP_"+str(response.status))
        buf=response.read(MAX_JSON_BYTES+1)
        if len(buf)>MAX_JSON_BYTES:
            raise RuntimeError("DRYAD_META_JSON_TOO_LARGE")
    obj=json.loads(buf.decode("utf-8"))
    if not isinstance(obj,dict):
        raise RuntimeError("DRYAD_META_NOT_A_JSON_OBJECT")
    return obj


def link_from(obj,key):
    x=obj.get("_links",{}).get(key)
    if not isinstance(x,dict) or not isinstance(x.get("href"),str):
        raise RuntimeError("DRYAD_EXPECTED_HAL_LINK_MISSING_"+key)
    return exact_api_url(x["href"])


def parse_files(data):
    embedded=data.get("_embedded")
    if not isinstance(embedded,dict) or not isinstance(embedded.get("stash:files"),list):
        raise RuntimeError("DRYAD_FILES_EMBEDDED_LIST_NOT_AVAILABLE")
    return embedded["stash:files"]


def audit(fetch=get_json):
    dataset=fetch(ENTRY)
    value=str(dataset.get("identifier") or "")
    if value.lower()!=DOI.lower():
        raise RuntimeError("ORIGINAL_BCI_DRYAD_DOI_MISMATCH")
    version_url=link_from(dataset,"stash:version")
    version=fetch(version_url)
    files_url=link_from(version,"stash:files")
    if not files_url.endswith("/files") and "/files?" not in files_url:
        raise RuntimeError("DRYAD_UNEXPECTED_VERSION_FILES_ENDPOINT")
    files=[]
    seen=set()
    url=files_url
    pages=0
    declared_total=None
    while url:
        pages+=1
        if pages>MAX_PAGES:raise RuntimeError("DRYAD_FILE_PAGE_LIMIT_EXCEEDED")
        page=fetch(url)
        if not isinstance(page.get("total"),int):
            raise RuntimeError("DRYAD_FILE_LIST_TOTAL_NOT_EXPLICIT")
        if declared_total is None:declared_total=page["total"]
        if declared_total!=page["total"]:raise RuntimeError("DRYAD_FILE_LIST_TOTAL_CHANGED")
        for item in parse_files(page):
            if not isinstance(item,dict) or not isinstance(item.get("id"),int):
                raise RuntimeError("DRYAD_FILE_ID_NOT_PUBLIC_INT")
            fid=item["id"]
            if fid in seen:raise RuntimeError("DRYAD_DUPLICATE_PAGINATED_FILE_ID")
            seen.add(fid)
            name=item.get("path")
            if not isinstance(name,str) or not name.strip():
                raise RuntimeError("DRYAD_FILE_PATH_MISSING")
            size=item.get("size")
            if not isinstance(size,int) or size<0:
                raise RuntimeError("DRYAD_FILE_SIZE_INVALID")
            files.append({
              "public_file_id":fid,
              "public_path":name,
              "file_bytes":size,
              "mimeType":item.get("mimeType"),
              "digest_type":item.get("digestType"),
              "digest":item.get("digest"),
              "actual_file_content_downloaded":False
            })
        nxt=page.get("_links",{}).get("next")
        url=exact_api_url(nxt["href"]) if isinstance(nxt,dict) and isinstance(nxt.get("href"),str) else None
    if not files or declared_total!=len(files):
        raise RuntimeError("DRYAD_TOTAL_FILES_MISMATCH_OR_EMPTY")
    totalbytes=sum(x["file_bytes"] for x in files)
    declared_storage=dataset.get("storageSize")
    size_matches=None if not isinstance(declared_storage,int) else totalbytes==declared_storage
    if size_matches is False:
        raise RuntimeError("DRYAD_DATASET_VERSION_STORAGE_SIZE_DRIFT")
    return {
       "schema_version":1,
       "status":SOURCE_PASS,
       "created_utc":datetime.now(timezone.utc).isoformat(),
       "frozen_design":DESIGN,
       "original_Dryad_dataset_DOI":value,
       "dataset_id":dataset.get("id"),
       "dataset_title":dataset.get("title"),
       "dataset_publication_date":dataset.get("publicationDate"),
       "current_version_id":version.get("id"),
       "current_version_number":version.get("versionNumber"),
       "current_version_status":version.get("versionStatus"),
       "publisher_declared_storage_bytes":declared_storage,
       "listed_version_file_bytes":totalbytes,
       "listed_bytes_match_dataset_storage_size":size_matches,
       "current_version_files_reported":declared_total,
       "file_listing_pages":pages,
       "public_file_metadata":files,
       "source_Dryad_API_only_no_original_files_downloaded":True,
       "biological_plant_rows_or_plot_coordinates_read":False,
       "no_GBIF_or_bat_record_opened":True,
       "independent_35_or_106_plant_taxa_overlap_estimated":False,
       "real_M3_minus_M1_bat_auc":None,
       "single_BCI_locality_only_not_regional_replication":True,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="docs/replication/neobat/bci_dryad_2026_file_metadata.json")
    args=parser.parse_args()
    dst=pathlib.Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True)
    try:receipt=audit()
    except Exception as exc:
        receipt={
          "schema_version":1,
          "status":"EXTERNAL_BCI_DRYAD_METADATA_SOURCE_STOP",
          "error_type":type(exc).__name__,
          "error_code":str(exc)[:220],
          "original_Dryad_dataset_DOI":DOI,
          "biological_plant_rows_or_plot_coordinates_read":False,
          "real_M3_minus_M1_bat_auc":None
        }
    dst.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_EXTERNAL_BCI_DRYAD_METADATA",receipt["status"],flush=True)
    if "current_version_files_reported" in receipt:
        print("DRYAD_FILE_COUNT",receipt["current_version_files_reported"],
              "VERSION",receipt["current_version_id"],flush=True)
    return 0 if receipt["status"]==SOURCE_PASS else 3


if __name__=="__main__":
    raise SystemExit(main())
