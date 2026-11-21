"""Test bat×country potential fruit-resource predictor inputs from full GBIF source QC.

All results are record-derived source feasibility, NOT an ecological SDM fit.
No raw GBIF occurrence records or exact coordinates are opened in this stage.
"""
from __future__ import annotations

import argparse, json, pathlib
from collections import defaultdict
from datetime import datetime, timezone

from scripts import neobat_gbif_metadata_preflight as neobat
from scripts import neobat_spatial_cell_pilot as grid
from scripts.neobat_resource_country_gate import COUNTRY_CODE
from scripts.neobat_summarize_full_source_qc import EXPECTED

GROUPS=("bat","plant")
MODE_SPEC={
    "strict":"precision_le12500m_25km_cells",
    "all":"recorded_25km_cells"
}
NAMES={
    "bat":"CurrentBatSpecies","plant":"CurrentPlantSpecies"
}

def source_validate(q):
    if q.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise ValueError("SOURCE_QC_NOT_COMPLETE")
    if set(q.get("groups",{}))!=set(GROUPS):
        raise ValueError("GROUPS_NOT_COMPLETE")
    for g in GROUPS:
        d=q["groups"][g]
        pin=EXPECTED[g]
        if (d.get("DOI")!=pin["doi"] or
            d.get("source_archive_sha256")!=pin["archive_sha"] or
            d.get("full_archive_rows_checked")!=pin["n_records"]):
            raise ValueError("SOURCE_QC_DOI_SHA_ROW_MISMATCH_"+g)
        if len(d.get("species_summary",[]))!=pin["n_species"]:
            raise ValueError("SOURCE_COHORT_TAXA_MISMATCH_"+g)
    return True

def build(q, records, sites, refs):
    source_validate(q)
    if len(sites)!=len({r["SiteCode"] for r in sites}):
        raise ValueError("SITE_KEY_DUPLICATED")
    bysite={r["SiteCode"]:r for r in sites}
    if set(s["Country"] for s in sites).difference(COUNTRY_CODE):
        raise ValueError("MISSING_COUNTRY_MAPPING")
    audit=neobat.audit({"records":records,"sites":sites,"references":refs})
    bats=sorted(x["bat"] for x in audit["species"] if x["primary_candidate"])
    if len(bats)!=26:raise ValueError("FROZEN_26_BAT_DENOMINATOR_STOP")
    plants=set(x["taxon"] for x in q["groups"]["plant"]["species_summary"])
    bat_roster=set(x["taxon"] for x in q["groups"]["bat"]["species_summary"])
    if set(bats)!=bat_roster or len(plants)!=255:
        raise ValueError("GBIF_SOURCE_TAXON_ROSTER_MISMATCH")
    all_countries=sorted(grid.LATAM)
    refs_by_country=defaultdict(set)
    for s in sites:refs_by_country[COUNTRY_CODE[s["Country"]]].add(s["RefCode"])
    links=[]
    for r in records:
        if r["Interaction"]!="Frugivory" or r["TrophicGuild"]!="Frugivore":
            continue
        bat,plant=r["CurrentBatSpecies"],r["CurrentPlantSpecies"]
        if bat not in bat_roster or plant not in plants:
            continue
        site=bysite.get(r["SiteCode"])
        if not site or site["RefCode"]!=r["RefCode"]:
            raise ValueError("BROKEN_SITE_TO_REF_PROVENANCE")
        links.append((bat,plant,r["RefCode"],COUNTRY_CODE[site["Country"]]))
    # Full-source cells by indexed taxon and country. No raw location material.
    bygroup={}
    for group in GROUPS:
        bygroup[group]={(r["taxon"],r["country"]):r
                        for r in q["groups"][group]["species_country_summary"]}
    if any(cc not in grid.LATAM for d in bygroup.values() for (_,cc) in d):
        raise ValueError("GBIF_COUNTRY_OUTSIDE_PINNED_QUERY")
    output={}
    for mode,col in MODE_SPEC.items():
        bybat={}
        for bat in bats:
            region=[]
            total=sum(bygroup["bat"].get((bat,cc),{}).get(col,0)
                      for cc in all_countries)
            source_links=[l for l in links if l[0]==bat]
            for country in all_countries:
                source_count=bygroup["bat"].get((bat,country),{}).get(col,0)
                outside=total-source_count
                if source_count<5 or outside<20:
                    continue
                banned=refs_by_country[country]
                trained=[(plant,ref) for _,plant,ref,src_country in source_links
                         if src_country!=country and ref not in banned]
                partners=sorted({plant for plant,ref in trained
                                 if bygroup["plant"].get((plant,country),{}).get(col,0)>=5})
                refs_retained={ref for plant,ref in trained if plant in partners}
                eligible=len(partners)>=3 and len(refs_retained)>=2
                region.append({
                    "country":country,
                    "recorded_bat_cells":source_count,
                    "outside_country_bat_cells":outside,
                    "training_partner_plant_names":len({p for p,r in trained}),
                    "plants_with_5plus_local_recorded_cells":len(partners),
                    "source_training_references_covering_local_plants":len(refs_retained),
                    "input_possible":eligible,
                    "status":"RESOURCE_SOURCE_INPUT_POSSIBLE" if eligible else "INPUT_INDETERMINATE"
                })
            bybat[bat]={
                "bat":bat,
                "bat_countries_with_5plus_cells_and_20plus_outside":len(region),
                "countries_with_3plus_local_plant_partners_2plus_refs":sum(x["input_possible"] for x in region),
                "country_records":region
            }
        output[mode]={
            "mode":mode,
            "definition":"recorded cells with reported coordinateUncertainty <=12.5km" if mode=="strict"
                else "all GBIF indexed coordinates (including missing uncertainty)",
            "bats_with_any_country_input_possible":sum(
                x["countries_with_3plus_local_plant_partners_2plus_refs"]>=1 for x in bybat.values()),
            "bats_with_2plus_countries_input_possible":sum(
                x["countries_with_3plus_local_plant_partners_2plus_refs"]>=2 for x in bybat.values()),
            "bat_country_pairs_with_5plus_bat_cells_20plus_outside":sum(
                x["bat_countries_with_5plus_cells_and_20plus_outside"] for x in bybat.values()),
            "bat_country_pairs_with_source_partner_input":sum(
                x["countries_with_3plus_local_plant_partners_2plus_refs"] for x in bybat.values()),
            "all_26_bats":list(bybat.values())
        }
    missing_plants=sorted(x["taxon"] for x in q["groups"]["plant"]["species_summary"]
                          if x["country_cells"]==0)
    return {
        "schema_version":1,
        "status":"FULL_DOI_PRECISION_CONDITIONED_INPUT_FEASIBILITY_ONLY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source_neobat_commit":neobat.COMMIT,
        "source_bat_DOI":EXPECTED["bat"]["doi"],
        "source_plant_DOI":EXPECTED["plant"]["doi"],
        "initial_bats":26,"initial_plants":255,
        "source_frugivory_primary_rows_matched_both_accepted_taxa":len(links),
        "plant_species_with_no_indexed_cells":missing_plants,
        "actual_plant_resource_availability_observed":False,
        "species_country_cell_cooccurrence_tested":False,
        "recorded_cells_are_not_verified_occurrence":True,
        "independent_validation_not_performed":True,
        "M3_minus_M1":None,
        "modes":output
    }

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--source",default="docs/replication/neobat/gbif_full_source_qc.json")
    pa.add_argument("--out",default="docs/replication/neobat/gbif_precision_resource_country_gate.json")
    args=pa.parse_args()
    dst=pathlib.Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        full=json.loads(pathlib.Path(args.source).read_text())
        tbl={}
        for key in neobat.FILES:
            tbl[key],meta=neobat.read_source(key)
        result=build(full,tbl["records"],tbl["sites"],tbl["references"])
    except Exception as exc:
        result={"schema_version":1,"status":"PRECISION_RESOURCE_INPUT_GATE_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:220],
                "M3_minus_M1":None}
    dst.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for mode,x in result.get("modes",{}).items():
        print("MODE",mode,
              "candidate_bats",x["bats_with_2plus_countries_input_possible"],
              "source_qualified_pairs",x["bat_country_pairs_with_source_partner_input"],flush=True)
    print("NEOBAT_FULL_DOI_RESOURCE_INPUT",result["status"],flush=True)
    return 0 if result["status"]=="FULL_DOI_PRECISION_CONDITIONED_INPUT_FEASIBILITY_ONLY" else 3

if __name__=="__main__":
    raise SystemExit(main())
