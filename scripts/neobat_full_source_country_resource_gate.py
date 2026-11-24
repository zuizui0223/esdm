"""Prefit country/fruit-resource input gate from complete DOI-backed GBIF cell QC.

Uses pre-aggregated species-country counts + original author NeoBat links.
Does not fit plant/bat SDMs, claim absences, or inspect held-out responses.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import defaultdict, Counter
from datetime import datetime, timezone

from scripts import neobat_gbif_metadata_preflight as neo
from scripts import neobat_resource_country_gate as old
from scripts import neobat_spatial_cell_pilot as spatial

COUNTRIES=tuple(sorted(spatial.LATAM))
BATS=26
PLANTS=255

def index(group):
    idx={};total=defaultdict(lambda:{"all":0,"strict":0})
    for row in group["species_country_summary"]:
        key=(row["taxon"],row["country"])
        if key in idx: raise ValueError("DUPLICATE_TAXON_COUNTRY")
        if key[1] not in COUNTRIES: raise ValueError("UNAUTHORIZED_COUNTRY")
        v=row["recorded_25km_cells"]
        p=row["precision_le12500m_25km_cells"]
        if not all(isinstance(x,int) and x>=0 for x in (v,p)) or p>v:
            raise ValueError("INVALID_CELL_COUNTS")
        idx[key]=row;total[key[0]]["all"]+=v;total[key[0]]["strict"]+=p
    return idx,total

def cells(idx,total,taxon,country,mode):
    r=idx.get((taxon,country),{})
    col="recorded_25km_cells" if mode=="all" else "precision_le12500m_25km_cells"
    within=r.get(col,0)
    return within,total[taxon][mode]-within

def calculate(qc, records, sites, bat_names, plant_names, enforce_roster=True):
    if qc.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise ValueError("INCOMPLETE_DOI_QC")
    if set(qc.get("groups",{}))!={"bat","plant"}:
        raise ValueError("MISSING_GROUP")
    if enforce_roster:
        for group, names, expected in (
            ("bat",bat_names,BATS),("plant",plant_names,PLANTS)):
            present={r["taxon"] for r in qc["groups"][group]["species_summary"]}
            if len(names)!=expected or present!=set(names):
                raise ValueError("TAXON_COHORT_MISMATCH_"+group)
        # Check the 26 bats are still the original source-only selection.
        refs=[{"RefCode":r} for r in sorted({s["RefCode"] for s in sites})]
        q=neo.audit({"records":records,"sites":sites,"references":refs})
        primary={r["bat"] for r in q["species"] if r["primary_candidate"]}
        if primary!=set(bat_names):
            raise ValueError("NEOBAT_PRIMARY_COHORT_MISMATCH")
    if set(s["Country"] for s in sites)-set(old.COUNTRY_CODE):
        raise ValueError("UNKNOWN_NEOBAT_SITE_COUNTRY")
    site={s["SiteCode"]:s for s in sites}
    if len(site)!=len(sites): raise ValueError("DUPLICATE_SITE_CODE")
    embargo=defaultdict(set)
    for s in sites:
        embargo[old.COUNTRY_CODE[s["Country"]]].add(s["RefCode"])
    edges=defaultdict(list);source_n=0
    for r in records:
        if r.get("Interaction")!="Frugivory" or r.get("TrophicGuild")!="Frugivore":
            continue
        if r.get("CurrentBatSpecies") not in bat_names:
            continue
        s=site.get(r["SiteCode"])
        if s is None or s["RefCode"]!=r["RefCode"]:
            raise ValueError("INVALID_SOURCE_EVENT_LINK")
        if r["CurrentPlantSpecies"] in plant_names:
            edges[r["CurrentBatSpecies"]].append((
                r["CurrentPlantSpecies"],r["RefCode"],
                old.COUNTRY_CODE[s["Country"]]))
            source_n+=1
    batidx,battotal=index(qc["groups"]["bat"])
    plantidx,planttotal=index(qc["groups"]["plant"])
    result=[];counts=defaultdict(Counter)
    for bat in sorted(bat_names):
        for country in COUNTRIES:
            links=defaultdict(set)
            for plant,ref,src_country in edges[bat]:
                if src_country!=country and ref not in embargo[country]:
                    links[plant].add(ref)
            entry={"bat":bat,"country":country,"indexed":None,"known_precision":None}
            for mode,outname in (("all","indexed"),("strict","known_precision")):
                inside,outside=cells(batidx,battotal,bat,country,mode)
                bat_ok=inside>=5 and outside>=20
                viable_pool={plant for plant in plant_names
                             if (lambda a,b:a>=5 and b>=20)(
                                 *cells(plantidx,planttotal,plant,country,mode))}
                viable=sorted(viable_pool.intersection(links))
                refs=set()
                for plant in viable: refs.update(links[plant])
                admitted=bat_ok and len(viable)>=3 and len(refs)>=2
                reason=("BAT_COUNTRY_CELLS_INSUFFICIENT" if not bat_ok else
                        "PARTNER_PLANT_CELLS_INSUFFICIENT" if len(viable)<3 else
                        "INDEPENDENT_SOURCE_REFERENCES_INSUFFICIENT" if len(refs)<2
                        else "PREFIT_INPUT_CANDIDATE")
                entry[outname]={
                    "bat_25km_cells_in_country":inside,
                    "bat_25km_cells_outside_country":outside,
                    "bat_cell_requirement_met":bat_ok,
                    "plant_pool_species_meeting_5_20":len(viable_pool),
                    "training_source_linked_plant_species":len(links),
                    "linked_plant_species_meeting_5_20":len(viable),
                    "independent_outcountry_NeoBat_refs":len(refs),
                    "nonpartner_pool_species_meeting_5_20":len(viable_pool-set(links)),
                    "eligible_partner_names":viable if (mode=="strict" and admitted) else [],
                    "status":reason,"input_candidate":admitted}
                counts[bat][outname+"_candidate_folds"]+=int(admitted)
                counts[bat][outname+"_bat_supported_folds"]+=int(bat_ok)
            result.append(entry)
    report={
        "schema_version":1,
        "status":"PREFIT_DOI_COUNTRY_RESOURCE_INPUT_ONLY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "bat_species":len(bat_names),"plant_species":len(plant_names),
        "countries":len(COUNTRIES),"total_bat_country_pairs":len(result),
        "source_link_rows_after_exact_name_mapping":source_n,
        "gates":{"bat_cells_in_country":5,"bat_cells_outside":20,
                 "plant_cells_in_country":5,"plant_cells_outside":20,
                 "linked_plants":3,"independent_refs":2},
        "indexed_source_candidate_pairs":sum(x["indexed"]["input_candidate"] for x in result),
        "known_precision_source_candidate_pairs":sum(x["known_precision"]["input_candidate"] for x in result),
        "bats_with_two_or_more_indexed_candidate_countries":sum(
            z["indexed_candidate_folds"]>=2 for z in counts.values()),
        "bats_with_two_or_more_known_precision_candidate_countries":sum(
            z["known_precision_candidate_folds"]>=2 for z in counts.values()),
        "DOIs":{"bat":"10.15468/dl.nxu727","plant":"10.15468/dl.xwc5zf"},
        "country_cooccurrence_not_confirmed":True,
        "plant_SDM_not_fitted":True,
        "independent_response_holdout_unverified":True,
        "ecological_M3_minus_M1":None,
        "by_bat_counts":{b:dict(x) for b,x in sorted(counts.items())},
        "folds":result}
    return report

def compact(full):
    if full["status"]!="PREFIT_DOI_COUNTRY_RESOURCE_INPUT_ONLY":
        raise ValueError("FULL_GATE_NOT_COMPLETED")
    bybat=[]
    for bat,stat in full["by_bat_counts"].items():
        known=[x["country"] for x in full["folds"]
               if x["bat"]==bat and x["known_precision"]["input_candidate"]]
        bybat.append({
            "bat":bat,"indexed_country_candidates":stat.get("indexed_candidate_folds",0),
            "known_precision_country_candidates":len(known),
            "known_precision_country_codes":known})
    bycountry=[]
    for c in COUNTRIES:
        r=[x for x in full["folds"] if x["country"]==c]
        bycountry.append({"country":c,
            "indexed_candidate_bats":sum(x["indexed"]["input_candidate"] for x in r),
            "known_precision_candidate_bats":sum(x["known_precision"]["input_candidate"] for x in r),
            "known_precision_bats_with_5_inside_20_outside":sum(
                x["known_precision"]["bat_cell_requirement_met"] for x in r)})
    return {
        "schema_version":1,"status":"PREFIT_DOI_COUNTRY_RESOURCE_COMPACT",
        "created_utc":full["created_utc"],
        "denominators":{"bats":full["bat_species"],"plants":full["plant_species"],
                        "countries":full["countries"],"bat_country":full["total_bat_country_pairs"]},
        "gates":full["gates"],"source_rows":full["source_link_rows_after_exact_name_mapping"],
        "candidate_pairs_indexed":full["indexed_source_candidate_pairs"],
        "candidate_pairs_known_precision":full["known_precision_source_candidate_pairs"],
        "bats_with_two_or_more_indexed_candidate_countries":
            full["bats_with_two_or_more_indexed_candidate_countries"],
        "bats_with_two_or_more_known_precision_candidate_countries":
            full["bats_with_two_or_more_known_precision_candidate_countries"],
        "DOIs":full["DOIs"],
        "cooccurrence_and_M3_effect_not_evaluated":True,
        "by_bat":bybat,"by_country":bycountry}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--full-qc",default="docs/replication/neobat/gbif_full_source_qc.json")
    p.add_argument("--bat-meta",default="docs/replication/neobat/gbif_search_preflight.json")
    p.add_argument("--plant-meta",default="docs/replication/neobat/plant_search_preflight.json")
    p.add_argument("--out",default="build/neobat/doi_country_resource_input.json")
    p.add_argument("--compact",default="build/neobat/doi_country_resource_compact.json")
    args=p.parse_args()
    out=pathlib.Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    small=pathlib.Path(args.compact);small.parent.mkdir(parents=True,exist_ok=True)
    try:
        full=json.loads(pathlib.Path(args.full_qc).read_text())
        b=json.loads(pathlib.Path(args.bat_meta).read_text())
        a=json.loads(pathlib.Path(args.plant_meta).read_text())
        bats=[r["bat"] for r in b["records"] if r["status"] in
              ("GBIF_COUNTS_ONLY","GBIF_COUNTS_AUDITED_ALIAS")]
        plants=[r["plant"] for r in a["plants"] if r["status"]=="GBIF_PLANT_COUNTS_ONLY"]
        rec,rec_meta=neo.read_source("records")
        sites,site_meta=neo.read_source("sites")
        report=calculate(full,rec,sites,bats,plants)
        report["source_sha256"]={"records":rec_meta["sha256"],"sites":site_meta["sha256"]}
        summary=compact(report);summary["source_sha256"]=report["source_sha256"]
    except Exception as exc:
        report={"schema_version":1,"status":"SOURCE_INPUT_GATE_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:240],
                "ecological_M3_minus_M1":None}
        summary=report.copy()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    small.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print("DOI_RESOURCE_COUNTRY",summary["status"],
          "broad",summary.get("candidate_pairs_indexed"),
          "strict",summary.get("candidate_pairs_known_precision"),flush=True)
    return 0 if summary["status"]=="PREFIT_DOI_COUNTRY_RESOURCE_COMPACT" else 3

if __name__=="__main__":sys.exit(main())
