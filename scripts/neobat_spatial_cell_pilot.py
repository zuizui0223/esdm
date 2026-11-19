"""GBIF coordinate-cell feasibility pilot, fixed 4 bats + 10 fruit plants.

No DOI-bearing GBIF download, ecological fit, heldout scoring or absence claims.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pyproj import Transformer

BATS = (
    "Carollia perspicillata", "Artibeus lituratus",
    "Artibeus jamaicensis", "Artibeus planirostris",
)
PLANTS = (
    "Cecropia obtusifolia", "Cecropia obtusa", "Ficus insipida",
    "Ficus yoponensis", "Solanum rugosum", "Piper aduncum",
    "Ficus citrifolia", "Cecropia ficifolia", "Ficus trigonata",
    "Ficus popenoei",
)
LATAM = {
    'AR','BO','BR','BZ','CL','CO','CR','CU','CW','DO','EC','GF','GT','GY',
    'HN','HT','JM','MX','NI','PA','PE','PR','PY','SR','SV','TT','UY','VE','BS'
}
PARAMS = {
    "hasCoordinate":"true", "hasGeospatialIssue":"false", "year":"2000,2025",
    "occurrenceStatus":"PRESENT", "limit":300
}
TRANS = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)


def gbif_get(params: dict) -> dict:
    url = 'https://api.gbif.org/v1/occurrence/search?' + urlencode(params)
    req = Request(url, headers={
        "Accept":"application/json",
        "User-Agent":"esdm-NeoBat-source-spatial-preflight/2026-11-19 (https://github.com/zuizui0223/esdm)"
    })
    errors=[]
    for attempt in range(3):
        try:
            with urlopen(req,timeout=45) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (OSError, HTTPError, ValueError) as exc:
            errors.append(type(exc).__name__+': '+str(exc)[:100])
            if attempt<2:
                time.sleep([2,5][attempt])
    raise RuntimeError("REMOTE_STOP: "+ "; ".join(errors))


def choose_taxa(batmeta: dict, plantmeta: dict):
    bat={r['bat']:r for r in batmeta.get('records',[])}
    plant={r['plant']:r for r in plantmeta.get('plants',[])}
    selected=[]
    for group,names,source,valid in (
        ("bat",BATS,bat,{"GBIF_COUNTS_ONLY","GBIF_COUNTS_AUDITED_ALIAS"}),
        ("plant",PLANTS,plant,{"GBIF_PLANT_COUNTS_ONLY"}),
    ):
        for name in names:
            if name not in source:
                raise RuntimeError("MISSING_PINNED_TAXON_STOP:"+name)
            row=source[name]
            if row.get('status') not in valid:
                raise RuntimeError("TAXON_NOT_ADMITTED_STOP:"+name)
            m=row.get("match") or {}
            key=m.get("acceptedUsageKey") or m.get("usageKey")
            if not key or m.get("rank")!="SPECIES":
                raise RuntimeError("TAXON_KEY_OR_RANK_STOP:"+name)
            selected.append({"group":group,"name":name,"taxonKey":int(key),
                             "GBIF_taxon_status":m.get("status"),
                             "metadata_country_count_upper_bound":row.get("regional_records_upper_bound"),
                             "metadata_world_records":row.get("world_records")})
    return selected


def label_precision(v):
    if v is None or v == "":
        return "missing"
    try:
        x=float(v)
        if not math.isfinite(x) or x<0:
            return "missing"
        return "known_le_12_5km" if x<=12500 else "known_gt_12_5km"
    except (TypeError, ValueError):
        return "missing"


def spatial_grid(lon,lat):
    if not (math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90):
        return None
    x,y=TRANS.transform(lon,lat)
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return ((math.floor(x/25000),math.floor(y/25000)),
            (math.floor(x/50000),math.floor(y/50000)))


def audit_species(descriptor:dict, pace:float=.10) -> dict:
    name=descriptor['name'];key=descriptor['taxonKey'];group=descriptor['group']
    row=dict(descriptor)
    counts=Counter()
    country_records=Counter()
    dataset_by_country=defaultdict(set)
    cell25_by_country=defaultdict(set)
    cell50_by_country=defaultdict(set)
    strict25_by_country=defaultdict(set)
    strict50_by_country=defaultdict(set)
    b=Counter()
    count=None;offset=0
    try:
        while True:
            params=dict(PARAMS,taxonKey=str(key),offset=offset)
            page=gbif_get(params)
            if 'count' not in page or not isinstance(page.get('results'),list):
                raise RuntimeError('RESPONSE_SCHEMA_STOP')
            if count is None:
                count=int(page['count'])
                if count>100000:
                    raise RuntimeError('API_100K_LIMIT_STOP')
            if page['count']!=count:
                raise RuntimeError('QUERY_COUNT_DRIFT_STOP')
            found=page['results']
            if not found and offset<count:
                raise RuntimeError('EARLY_EMPTY_PAGE_STOP')
            for rec in found:
                counts['rows_seen']+=1
                cc=str(rec.get('countryCode') or '')
                if cc not in LATAM:
                    counts['outside_country_proxy']+=1
                    continue
                counts['country_proxy_rows']+=1
                country_records[cc]+=1
                dataset=rec.get('datasetKey')
                if dataset:
                    dataset_by_country[cc].add(str(dataset))
                b[str(rec.get('basisOfRecord') or 'UNKNOWN')]+=1
                try:
                    lon=float(rec.get('decimalLongitude'))
                    lat=float(rec.get('decimalLatitude'))
                except (TypeError,ValueError):
                    counts['coordinate_invalid']+=1
                    continue
                loc=spatial_grid(lon,lat)
                if loc is None:
                    counts['coordinate_invalid']+=1
                    continue
                cell25,cell50=loc
                cell25_by_country[cc].add(cell25)
                cell50_by_country[cc].add(cell50)
                precision=label_precision(rec.get('coordinateUncertaintyInMeters'))
                counts['precision_'+precision]+=1
                if precision=='known_le_12_5km':
                    strict25_by_country[cc].add(cell25)
                    strict50_by_country[cc].add(cell50)
            offset+=len(found)
            if offset>=count:
                break
            if offset>100000:
                raise RuntimeError('API_100K_OFFSET_STOP')
            if pace:time.sleep(pace)
        row['status']='CELL_COUNTS_ONLY'
    except Exception as exc:
        row['status']='SPATIAL_PREFLIGHT_STOP'
        row['error']=str(exc)[:350]
    row.update(
        GBIF_live_count=count,
        records_processed=counts['rows_seen'],
        country_proxy_records=counts['country_proxy_rows'],
        outside_country_proxy_records=counts['outside_country_proxy'],
        coordinate_invalid=counts['coordinate_invalid'],
        coordinate_uncertainty_missing=counts['precision_missing'],
        known_le_12500m_records=counts['precision_known_le_12_5km'],
        known_gt_12500m_records=counts['precision_known_gt_12_5km'],
        country_basis_counts=dict(b),
        distinct_25km_cells=sum(len(a) for a in cell25_by_country.values()),
        distinct_50km_cells=sum(len(a) for a in cell50_by_country.values()),
        known_le_12500m_25km_cells=sum(len(a) for a in strict25_by_country.values()),
        known_le_12500m_50km_cells=sum(len(a) for a in strict50_by_country.values()),
        country_count_with_ge5_25km_cells=sum(len(a)>=5 for a in cell25_by_country.values()),
        country_count_with_ge5_known_accuracy_cells=sum(len(a)>=5 for a in strict25_by_country.values()),
        country_summary={
          c:{"records":country_records[c],
             "cells_25km":len(cell25_by_country[c]),
             "cells_50km":len(cell50_by_country[c]),
             "known_le_12500m_cells_25km":len(strict25_by_country[c]),
             "independent_datasetKeys":len(dataset_by_country[c])}
          for c in sorted(country_records)
        },
        citable_GBIF_download_DOI=None,
        independent_training_test_folds_certified=False,
        ecological_predictive_result=None,
    )
    return row


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument('--bat-metadata',default='docs/replication/neobat/gbif_search_preflight.json')
    pa.add_argument('--plant-metadata',default='docs/replication/neobat/plant_search_preflight.json')
    pa.add_argument('--out',default='build/neobat/spatial_cell_pilot.json')
    args=pa.parse_args()
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    try:
        b=json.loads(Path(args.bat_metadata).read_text())
        p=json.loads(Path(args.plant_metadata).read_text())
        taxa=choose_taxa(b,p)
        for idx,d in enumerate(taxa,1):
            result=audit_species(d)
            results.append(result)
            print(f"{idx}/{len(taxa)} {d['group']} {d['name']}: "+
                f"{result['status']} rows={result['records_processed']} "+
                f"25km_cells={result['distinct_25km_cells']}",flush=True)
        status='SPATIAL_CELLS_ONLY' if all(x['status']=='CELL_COUNTS_ONLY' for x in results) else 'SPATIAL_PILOT_PARTIAL_STOP'
    except Exception as exc:
        status='SPATIAL_PILOT_SOURCE_STOP'
        results.append({'status':status,'error':str(exc)[:350]})
    out={
        "schema_version":1,
        "status":status,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source":"GBIF occurrence SEARCH, not occurrence DOWNLOAD",
        "candidate_bats":list(BATS),"candidate_plants":list(PLANTS),
        "count_complete":sum(x['status']=='CELL_COUNTS_ONLY' for x in results),
        "candidate_total":len(BATS)+len(PLANTS),
        "bat_candidate_cell5_country_count_ge4":sum(x['group']=='bat' and x['country_count_with_ge5_25km_cells']>=4 for x in results if x['status']=='CELL_COUNTS_ONLY'),
        "DOI_bearing_download":False,
        "25km_cells_not_independent_occupancy":True,
        "independent_country_buffered_holdouts_validated":False,
        "ecological_result":None,
        "taxa":results
    }
    dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:out.get(k) for k in ('status','count_complete','candidate_total','bat_candidate_cell5_country_count_ge4')},indent=2),flush=True)
    return 0 if status=='SPATIAL_CELLS_ONLY' else 3

if __name__=='__main__':raise SystemExit(main())
