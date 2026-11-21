"""NeoBat country-aligned bat/fruit-partner *input* gate, no SDM prediction.

Consumes previously frozen GBIF SEARCH country-cell sampled lower bounds
and immutable author-source NeoBat tables. No occurrence coordinates saved.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts import neobat_gbif_metadata_preflight as sources
from scripts import neobat_spatial_cell_pilot as scope

COUNTRY_CODE = {
    "Brazil":"BR", "Costa Rica":"CR", "Mexico":"MX", "Venezuela":"VE",
    "Ecuador":"EC", "Panama":"PA", "French Guiana":"GF", "Peru":"PE",
    "United States":"US", "Colombia":"CO", "Cuba":"CU", "Bolivia":"BO",
    "Argentina":"AR", "Trinidad and Tobago":"TT", "Jamaica":"JM",
    "Curacao":"CW"
}

def supported(country_result):
    return (country_result.get("status") == "SAMPLED_LOWER_BOUND"
            and country_result.get("cell25_lower_bound", 0) >= 5)

def calculate(grid, records, sites):
    if grid.get("status") != "SAMPLED_CELL_LOWER_BOUND_COMPLETE":
        raise ValueError("MISSING_COMPLETE_BOUNDED_SAMPLE_STOP")
    if grid.get("target_species_count") != 14:
        raise ValueError("PILOT_TAXON_DENOMINATOR_STOP")
    if set(s["Country"] for s in sites).difference(COUNTRY_CODE):
        raise ValueError("UNMAPPED_NEOBAT_SITE_COUNTRY_STOP")
    site_by = {s["SiteCode"]: s for s in sites}
    if len(site_by) != len(sites):
        raise ValueError("DUPLICATE_SITECODE_STOP")
    ref_by_country = defaultdict(set)
    for s in sites:
        ref_by_country[COUNTRY_CODE[s["Country"]]].add(s["RefCode"])
    bat_grid = {t["name"]:t for t in grid["taxa"] if t.get("group")=="bat"}
    plant_grid = {t["name"]:t for t in grid["taxa"] if t.get("group")=="plant"}
    if set(bat_grid) != set(scope.BATS) or set(plant_grid) != set(scope.PLANTS):
        raise ValueError("PILOT_TAXON_ROSTER_MISMATCH_STOP")
    allowed_bats,allowed_plants=set(scope.BATS),set(scope.PLANTS)
    interactions = []
    for r in records:
        if r.get("Interaction")!="Frugivory" or r.get("TrophicGuild")!="Frugivore":
            continue
        if r.get("CurrentBatSpecies") not in allowed_bats or r.get("CurrentPlantSpecies") not in allowed_plants:
            continue
        s=site_by.get(r["SiteCode"])
        if s is None or r["RefCode"] != s["RefCode"]:
            raise ValueError("UNJOINED_INTERACTION_SOURCE_STOP")
        interactions.append({
            "bat":r["CurrentBatSpecies"],
            "plant":r["CurrentPlantSpecies"],
            "country":COUNTRY_CODE[s["Country"]],
            "ref":r["RefCode"]
        })
    cells={}
    for plant,g in plant_grid.items():
        cells[plant]={c["country"] for c in g["country_results"] if supported(c)}
    result=[]
    for bat in scope.BATS:
        g=bat_grid[bat]
        for item in g["country_results"]:
            country=item["country"]
            if not supported(item):
                result.append({
                    "bat":bat,"country":country,
                    "status":"BAT_NOT_SAMPLED_5_CELLS",
                    "eligible_resource_input":False
                })
                continue
            banned=ref_by_country.get(country,set())
            train=[e for e in interactions if e["bat"]==bat and
                   e["country"]!=country and e["ref"] not in banned]
            partners={e["plant"] for e in train}
            positive=sorted(p for p in partners if country in cells[p])
            refs={e["ref"] for e in train if e["plant"] in positive}
            eligible=len(positive)>=3 and len(refs)>=2
            result.append({
                "bat":bat, "country":country,
                "bat_sample_25km_cells_lower_bound":item["cell25_lower_bound"],
                "training_source_partner_names_in_pilot":len(partners),
                "positive_country_plant_sample_lower_bound":len(positive),
                "training_references_for_eligible_plants":len(refs),
                "partner_names":positive,
                "country_had_original_neobat_sites":bool(banned),
                "eligible_resource_input":eligible,
                "status":"PRELIMINARY_RESOURCE_INPUT_COMPATIBLE" if eligible
                         else "INDETERMINATE_10_PLANT_PILOT"
            })
    return {
        "schema_version":1,
        "status":"PREFIT_SOURCE_COUNTRY_INPUT_ONLY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source_neobat_commit":sources.COMMIT,
        "sampled_cell_receipt_created_utc":grid.get("created_utc"),
        "bat_species_count":len(scope.BATS),
        "plant_species_count":len(scope.PLANTS),
        "bat_country_combinations":len(result),
        "sampled_bat_country_combinations":sum(x["status"]!="BAT_NOT_SAMPLED_5_CELLS" for x in result),
        "countries_with_ge3_plant_links_ge2_outcountry_refs":sum(x["eligible_resource_input"] for x in result),
        "bats_with_at_least_two_resource_eligible_countries":sum(
            sum(x["bat"]==bat and x["eligible_resource_input"] for x in result)>=2
            for bat in scope.BATS),
        "number_original_frugivore_pilot_rows":len(interactions),
        "country_link_only_not_25km_cell_cooccurrence":True,
        "sampled_source_used_for_discovery_not_sealed_prediction":True,
        "full_GBIF_download_DOI":None,
        "M3_vs_M1_prediction_difference":None,
        "country_result":result
    }

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--grid-receipt", default="docs/replication/neobat/spatial_country_lb.json")
    pa.add_argument("--out", default="build/neobat/country_resource_gate.json")
    args=pa.parse_args()
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        grid=json.loads(Path(args.grid_receipt).read_text(encoding="utf-8"))
        record,src_rec=sources.read_source("records")
        sites,src_sites=sources.read_source("sites")
        out=calculate(grid,record,sites)
        out["source_data_sha256"]={"records":src_rec["sha256"],"sites":src_sites["sha256"]}
    except Exception as exc:
        out={"schema_version":1,"status":"SOURCE_OR_SCHEMA_STOP",
             "error":str(exc)[:300],"M3_vs_M1_prediction_difference":None}
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:out.get(k) for k in (
        "status","bat_country_combinations",
        "countries_with_ge3_plant_links_ge2_outcountry_refs",
        "bats_with_at_least_two_resource_eligible_countries",
        "error")},ensure_ascii=False),flush=True)
    return 0 if out["status"]=="PREFIT_SOURCE_COUNTRY_INPUT_ONLY" else 3

if __name__=="__main__":
    raise SystemExit(main())
