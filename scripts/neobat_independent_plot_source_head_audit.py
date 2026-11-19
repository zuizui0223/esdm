"""Read-only metadata/HEAD preflight for candidate independent plot & seed rain data.

Never GET biological data or download original archives. All external results
are only HTTP metadata, optional source accessibility signals; status failure
must never be reinterpreted as ecological absence. No credentials provided.
"""
from __future__ import annotations

import argparse,json,pathlib,urllib.request,urllib.error
from datetime import datetime,timezone

SOURCES=(
    ("sPlotOpen_full_zip","https://idata.idiv.de/ddm/Data/DownloadZip/3474?version=5047"),
    ("BIEN_4_2_plot_portal","https://bien.nceas.ucsb.edu/bien/biendata/"),
    ("Dryad_BCI_2026_dataset_meta","https://datadryad.org/dataset/doi:10.5061/dryad.1g1jwsvc3"),
    ("Smithsonian_BCI_seed_rain_2016_CSV","https://repository.si.edu/bitstreams/d2239f03-acd7-4c54-9224-ad20ce1a0fad/download"),
)
REGISTRY="docs/replication/NEOBAT_INDEPENDENT_BOTANICAL_SOURCE_REGISTRY_FROZEN_20261119.md"
MAX_REDIRECT_HOSTS={"idata.idiv.de","bien.nceas.ucsb.edu","datadryad.org",
                    "repository.si.edu","www.idiv.de"}


def probe(name,url,opener=None):
    opener=opener or urllib.request.urlopen
    request=urllib.request.Request(
        url,method="HEAD",
        headers={"User-Agent":"NeoBat-independent-plot-source-header-only/1.0",
                 "Accept":"*/*"})
    out={"name":name,"url":url,"request_method":"HEAD",
         "biological_response_bytes_read":0,
         "full_dataset_downloaded":False}
    try:
        with opener(request,timeout=18) as response:
            end=response.geturl()
            from urllib.parse import urlparse
            host=urlparse(end).hostname
            if host not in MAX_REDIRECT_HOSTS:
                # Record unusual redirect without inferring source trust.
                out["redirect_host_not_originally_allowlisted"]=True
            out.update({
                "status":"HEAD_HTTP_RESPONSE_ONLY",
                "http_status":response.status,
                "final_url":end,
                "content_type":response.headers.get("Content-Type"),
                "content_length":response.headers.get("Content-Length"),
                "last_modified":response.headers.get("Last-Modified"),
                "etag":response.headers.get("ETag"),
            })
    except urllib.error.HTTPError as error:
        out.update(status="HEAD_HTTP_STOP",http_status=error.code,
                   error_type=type(error).__name__)
    except Exception as error:
        out.update(status="HEAD_TRANSPORT_OR_TLS_STOP",
                   error_type=type(error).__name__,
                   error_code=str(error)[:160])
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/replication/neobat/independent_plot_source_head_audit.json")
    args=p.parse_args()
    if not pathlib.Path(REGISTRY).exists():
        raise SystemExit("FROZEN_SOURCE_REGISTRY_MISSING")
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    rows=[probe(k,url) for k,url in SOURCES]
    result={"schema_version":1,
            "status":"READ_ONLY_INDEPENDENT_BOTANICAL_SOURCE_HEAD_AUDIT",
            "created_utc":datetime.now(timezone.utc).isoformat(),
            "frozen_registry":REGISTRY,
            "HEAD_requests_only":True,
            "biological_records_read":0,
            "GBIF_response_or_fruit_species_table_opened":False,
            "independent_plot_species_overlap_estimated":False,
            "actual_raster_or_plant_model_fitted":False,
            "original_M3_minus_M1_auc":None,
            "source_probes":rows}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("INDEPENDENT_BOTANICAL_HEADER_GATE",result["status"])
    for row in rows:
        print("SOURCE",row["name"],row["status"],row.get("http_status"),
              row.get("content_length"))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
