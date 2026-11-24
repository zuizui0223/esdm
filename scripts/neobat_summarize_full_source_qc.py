"""Summarize existing full DOI-backed GBIF QC into a small inspectable receipt.

No raw GBIF records, coordinate lookup, network request or SDM fit. Never
change the source-cohort denominator based on observed cell support.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter
from datetime import datetime, timezone

EXPECTED={
    "bat":{"doi":"10.15468/dl.nxu727","n_records":85912,
           "archive_sha":"fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0",
           "n_species":26},
    "plant":{"doi":"10.15468/dl.xwc5zf","n_records":367988,
             "archive_sha":"4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b",
             "n_species":255}
}

def summarise(qc):
    if qc.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise ValueError("FULL_QC_NOT_COMPLETE")
    groups=qc.get("groups",{})
    if set(groups)!=set(EXPECTED):
        raise ValueError("GROUP_DENOMINATOR_STOP")
    compact={}
    for group,expect in EXPECTED.items():
        g=groups[group]
        if (g.get("DOI")!=expect["doi"] or
            g.get("source_archive_sha256")!=expect["archive_sha"] or
            g.get("full_archive_rows_checked")!=expect["n_records"]):
            raise ValueError("SOURCE_IDENTITY_MISMATCH_"+group)
        taxa=g.get("species_summary")
        country_rows=g.get("species_country_summary")
        if not isinstance(taxa,list) or len(taxa)!=expect["n_species"] or not isinstance(country_rows,list):
            raise ValueError("SPECIES_OR_COUNTRY_SCHEMA_STOP_"+group)
        by_taxon={}
        for entry in country_rows:
            by_taxon.setdefault(entry["taxon"],[]).append(entry)
        candidates=[]
        known=[]
        species_report=[]
        for t in taxa:
            name=t["taxon"]
            cs=by_taxon.get(name,[])
            all_count=sum(c["recorded_25km_cells"] for c in cs)
            strict_count=sum(c["precision_le12500m_25km_cells"] for c in cs)
            if all_count!=t["country_cells"] or strict_count!=t["known_precision_country_cells"]:
                raise ValueError("SPECIES_CELL_SUM_INCONSISTENCY_"+group)
            n_possible=sum(c["recorded_25km_cells"]>=5 and
                           all_count-c["recorded_25km_cells"]>=20 for c in cs)
            n_known=sum(c["precision_le12500m_25km_cells"]>=5 and
                        strict_count-c["precision_le12500m_25km_cells"]>=20 for c in cs)
            species_report.append({
                "taxon":name,"indexed_records":t["indexed_records_matching_species"],
                "country_cells_25km":all_count,
                "known_precision_country_cells_25km":strict_count,
                "countries_with_ge5_indexed_cells":t["countries_with_ge5_recorded_cells"],
                "countries_with_ge5_known_precision_cells":t["countries_with_ge5_known_precision_cells"],
                "countries_with_ge5_heldout_and20_outside_indexed_cells":n_possible,
                "countries_with_ge5_heldout_and20_outside_known_precision_cells":n_known
            })
            if n_possible>=2:candidates.append(name)
            if n_known>=2:known.append(name)
        bycountry={}
        for c in country_rows:
            cc=c["country"]
            obj=bycountry.setdefault(cc,{
                "species_with_5plus_indexed_cells":0,
                "species_with_5plus_known_precision_cells":0,
                "sum_species_country_indexed_25km_cells":0,
                "sum_species_country_known_precision_25km_cells":0
            })
            obj["species_with_5plus_indexed_cells"]+=(c["recorded_25km_cells"]>=5)
            obj["species_with_5plus_known_precision_cells"]+=(c["precision_le12500m_25km_cells"]>=5)
            obj["sum_species_country_indexed_25km_cells"]+=c["recorded_25km_cells"]
            obj["sum_species_country_known_precision_25km_cells"]+=c["precision_le12500m_25km_cells"]
        quality=g["quality_breakdown"]
        n_valid=int(g["valid_source_rows"])
        compact[group]={
            "status":g["status"],
            "doi":g["DOI"],"archive_sha256":g["source_archive_sha256"],
            "archive_rows":g["full_archive_rows_checked"],
            "valid_country_year_coordinate_rows":n_valid,
            "valid_record_fraction":round(n_valid/expect["n_records"],6),
            "quality_flags":quality,
            "species_in_complete_name_cohort":len(taxa),
            "species_with_at_least_1_recorded_cell":g["distinct_species_with_valid_cells"],
            "country_species_rows":len(country_rows),
            "sum_species_country_25km_recorded_cells":sum(c["recorded_25km_cells"] for c in country_rows),
            "sum_species_country_25km_known_precision_cells":sum(c["precision_le12500m_25km_cells"] for c in country_rows),
            "species_with_2plus_country_candidate_folds_indexed":len(candidates),
            "species_with_2plus_country_candidate_folds_known_precision":len(known),
            "candidate_country_folds_not_independent_validation":True,
            "countries":dict(sorted(bycountry.items())),
            "per_species":species_report if group=="bat" else [],
            "plant_species_eligibility_histogram":(dict(sorted(Counter(
                str(x["countries_with_ge5_heldout_and20_outside_known_precision_cells"])
                for x in species_report).items())) if group=="plant" else None),
            "all_source_candidate_names_retained":True
        }
    return {
        "schema_version":1,
        "status":"COMPLETE_SOURCE_QC_SUMMARY_NOT_MODEL",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "full_qc_read_from_same_pinned_archives":True,
        "GBIF_DOIs_minted":True,
        "source_exploratory_data_already_opened":True,
        "independent_holdout_unopened":False,
        "source_coordinate_grids_aggregated_only":True,
        "ecological_M3_minus_M1":None,
        "groups":compact
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="docs/replication/neobat/gbif_full_source_qc.json")
    p.add_argument("--out",default="docs/replication/neobat/gbif_full_source_qc_summary.json")
    args=p.parse_args()
    dst=pathlib.Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        full=json.loads(pathlib.Path(args.source).read_text())
        result=summarise(full)
    except Exception as exc:
        result={"schema_version":1,"status":"SOURCE_QC_SUMMARY_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:180],
                "ecological_M3_minus_M1":None}
    dst.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for group,g in result.get("groups",{}).items():
        print(group,"valid",g["valid_country_year_coordinate_rows"],
              "species",g["species_with_at_least_1_recorded_cell"],
              "2+ known-country-candidates",g["species_with_2plus_country_candidate_folds_known_precision"],flush=True)
    print("FULL_SOURCE_QC_COMPACT",result["status"],flush=True)
    return 0 if result["status"]=="COMPLETE_SOURCE_QC_SUMMARY_NOT_MODEL" else 3

if __name__=="__main__":
    sys.exit(main())
