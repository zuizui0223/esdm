"""Bounded, country-stratified lower-bound audit of GBIF 25/50 km cells.

14 source-predeclared taxa; up to four countries/taxon and one 300-record
SEARCH page/country. NOT a full record download or calibrated SDM.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts import neobat_spatial_cell_pilot as base

MAX_COUNTRIES = 4
LIMIT = 300
MAX_CONCURRENT = 3
MAX_SEARCH_PAGES = (len(base.BATS) + len(base.PLANTS)) * MAX_COUNTRIES
BUDGET_SECONDS = 650  # keep SEARCH audit well below GBIF's ~15-minute guidance

def selected_countries(record):
    """Preexisting *count-only* facet ranks, fixed before coordinate-page inspection."""
    c = record.get('regional_country_counts')
    if not isinstance(c, dict):
        raise ValueError("NO_COUNTRY_FACETS_STOP")
    choices = [(name, int(n)) for name, n in c.items()
               if name in base.LATAM and isinstance(n, (int, float))
               and math.isfinite(float(n)) and n >= 5]
    choices.sort(key=lambda x: (-x[1], x[0]))
    return choices[:MAX_COUNTRIES]

def get_page(params):
    url = "https://api.gbif.org/v1/occurrence/search?" + urlencode(params)
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "esdm-NeoBat-bounded-country-cell-preflight/20261119",
    })
    for attempt in range(2):
        try:
            with urlopen(request, timeout=22) as response:
                raw = response.read()
            return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                raise RuntimeError("GBIF_RATE_LIMIT_STOP") from exc
            if exc.code < 500 or attempt:
                raise RuntimeError("GBIF_HTTP_STOP:" + str(exc.code)) from exc
        except (URLError, OSError, ValueError) as exc:
            if attempt:
                raise RuntimeError("GBIF_PAGE_TRANSPORT_STOP:" + str(exc)[:120]) from exc
        if attempt == 0:
            time.sleep(2)
    raise RuntimeError("GBIF_PAGE_TRANSPORT_STOP: retries exhausted")

def audit_country(d, country, source_count):
    params = {
        **base.PARAMS,
        "taxonKey": str(d["taxonKey"]),
        "country": country,
        "offset": 0,
        "limit": LIMIT,
    }
    result = {"country": country, "source_facet_count": source_count,
              "status": "UNQUERIED", "records_seen": 0}
    try:
        response = get_page(params)
        if not isinstance(response, dict) or not isinstance(response.get("results"), list):
            raise ValueError("RESPONSE_SCHEMA_STOP")
        total = response.get("count")
        if not isinstance(total, int) or total < 0:
            raise ValueError("COUNT_SCHEMA_STOP")
        rows = response["results"]
        if len(rows) > LIMIT or (total > 0 and len(rows) == 0):
            raise ValueError("PAGE_LENGTH_SCHEMA_STOP")
        cell25, cell50, precision25, precision50, datasets = (
            set(), set(), set(), set(), set()
        )
        stats = Counter()
        for r in rows:
            stats["rows"] += 1
            if r.get("countryCode") != country:
                stats["country_mismatch"] += 1
                continue
            try:
                lat = float(r.get("decimalLatitude"))
                lon = float(r.get("decimalLongitude"))
            except (TypeError, ValueError):
                stats["bad_coordinate"] += 1
                continue
            if not (math.isfinite(lat) and math.isfinite(lon)):
                stats["bad_coordinate"] += 1
                continue
            cells = base.spatial_grid(lon, lat)
            if cells is None:
                stats["bad_coordinate"] += 1
                continue
            c25,c50 = cells
            cell25.add(c25)
            cell50.add(c50)
            if base.label_precision(r.get("coordinateUncertaintyInMeters")) == "known_le_12_5km":
                precision25.add(c25)
                precision50.add(c50)
                stats["known_precision_records"] += 1
            else:
                stats["missing_or_high_uncertainty"] += 1
            if r.get("datasetKey"):
                datasets.add(str(r["datasetKey"]))
        if stats["country_mismatch"]:
            raise ValueError("COUNTRY_RESPONSE_MISMATCH_STOP")
        result.update(
            status="SAMPLED_LOWER_BOUND",
            GBIF_country_live_total=total,
            records_seen=stats["rows"],
            cell25_lower_bound=len(cell25),
            cell50_lower_bound=len(cell50),
            cells25_with_reported_uncertainty_le_12500m=len(precision25),
            cells50_with_reported_uncertainty_le_12500m=len(precision50),
            reported_uncertainty_le_12500m_records=stats["known_precision_records"],
            other_uncertainty_records=stats["missing_or_high_uncertainty"],
            invalid_coordinate_records=stats["bad_coordinate"],
            dataset_keys_in_sample=len(datasets),
            page_limit=LIMIT,
            offset=0,
            fully_enumerated=(total == len(rows)),
            calibrated_occupancy=None
        )
    except Exception as exc:
        result.update(status="COUNTRY_PAGE_STOP", error=str(exc)[:220])
    return result

def run(batmeta, plantmeta, *, countries_fn=audit_country, budget_seconds=BUDGET_SECONDS):
    selected=base.choose_taxa(batmeta,plantmeta)
    b={r["bat"]:r for r in batmeta["records"]}
    p={r["plant"]:r for r in plantmeta["plants"]}
    planned=[]
    for d in selected:
        metadata = b[d["name"]] if d["group"] == "bat" else p[d["name"]]
        planned.append(dict(d, planned_countries=selected_countries(metadata)))
    start=time.monotonic()
    species=[]
    for i,d in enumerate(planned):
        if time.monotonic()-start >= budget_seconds:
            species.extend({**v,"status":"NOT_QUERIED_TIME_BUDGET",
                            "country_results":[]} for v in planned[i:])
            break
        cs=d["planned_countries"]
        outcomes={}
        if cs:
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as pool:
                futs={pool.submit(countries_fn, d, c, n):c for c,n in cs}
                for fut in as_completed(futs):
                    c=futs[fut]
                    try:
                        outcomes[c]=fut.result()
                    except Exception as exc:
                        outcomes[c]={"country":c,"status":"COUNTRY_PAGE_STOP","error":str(exc)[:180]}
        ordered=[outcomes[c] for c,n in cs]
        ready=[z for z in ordered if z["status"]=="SAMPLED_LOWER_BOUND"]
        sufficient=sum(z["cell25_lower_bound"]>=5 for z in ready)>=4
        species.append({
            "group":d["group"],"name":d["name"],"taxonKey":d["taxonKey"],
            "GBIF_count_metadata_upper_bound":d["metadata_country_count_upper_bound"],
            "selected_country_count":len(cs),
            "status":"SAMPLE_SUFFICIENT_4_COUNTRIES" if sufficient
                else ("PARTIAL_TRANSPORT_STOP" if len(ready)!=len(cs)
                      else "INDETERMINATE_FROM_BOUNDED_SAMPLE"),
            "sample_sufficient_4_countries":sufficient,
            "reported_uncertainty_sufficient_4_countries":sum(
                z.get("cells25_with_reported_uncertainty_le_12500m",0)>=5 for z in ready)>=4,
            "country_results":ordered
        })
    all_pages=[c for s in species for c in s.get("country_results",[])]
    n_attempts=len(all_pages)
    errors=sum(c["status"]!="SAMPLED_LOWER_BOUND" for c in all_pages)
    status="SAMPLED_CELL_LOWER_BOUND_COMPLETE" if (
        len(species)==len(selected) and errors==0 and
        all(s["status"]!="NOT_QUERIED_TIME_BUDGET" for s in species)
    ) else "PARTIAL_SAMPLE_TRANSPORT_STOP"
    return {
        "schema_version":1, "status":status,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "method":"first GBIF SEARCH page, up to 4 highest-count countries per original taxon",
        "source_bat_name_count":len(base.BATS),
        "source_plant_name_count":len(base.PLANTS),
        "target_species_count":len(selected),
        "country_pages_attempted":n_attempts,"country_pages_max":MAX_SEARCH_PAGES,
        "country_pages_completed":n_attempts-errors,
        "sufficient_lower_bound_bats":sum(s.get("group")=="bat" and s.get("sample_sufficient_4_countries",False) for s in species),
        "sufficient_lower_bound_plants":sum(s.get("group")=="plant" and s.get("sample_sufficient_4_countries",False) for s in species),
        "same_pilot_14_taxa_as_frozen_exhaustive_design":True,
        "sample_not_random":True,"not_a_census":True,
        "GBIF_DOWNLOAD_DOI":None,"independent_occurrence_folds":False,
        "ecological_predictive_effect":None,"taxa":species
    }

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--bat-metadata",default="docs/replication/neobat/gbif_search_preflight.json")
    pa.add_argument("--plant-metadata",default="docs/replication/neobat/plant_search_preflight.json")
    pa.add_argument("--out",default="build/neobat/spatial_country_lb.json")
    args=pa.parse_args()
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    inputs={}
    try:
        bat=Path(args.bat_metadata).read_bytes()
        plant=Path(args.plant_metadata).read_bytes()
        inputs={"bat_sha256":hashlib.sha256(bat).hexdigest(),
                "plant_sha256":hashlib.sha256(plant).hexdigest()}
        # Open no occurrence responses if metadata source is malformed.
        d=run(json.loads(bat),json.loads(plant))
    except Exception as exc:
        d={"schema_version":1,"status":"SOURCE_OR_IMPLEMENTATION_STOP",
           "error":str(exc)[:240],"ecological_predictive_effect":None}
    d["input_source_hashes"]=inputs
    dest.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:d.get(k) for k in (
        "status","target_species_count","country_pages_attempted",
        "country_pages_completed","sufficient_lower_bound_bats",
        "sufficient_lower_bound_plants","error")},ensure_ascii=False),flush=True)
    return 0 if d["status"]=="SAMPLED_CELL_LOWER_BOUND_COMPLETE" else 3

if __name__=="__main__":
    raise SystemExit(main())
