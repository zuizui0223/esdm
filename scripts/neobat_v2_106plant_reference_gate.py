"""Exploratory NeoBat v2: fixed globally trainable plant pool + partner/N1 gates.

Uses existing original DOI aggregate plant cells and immutable author NeoBat
reference sources, never GBIF bat responses or new full occurrences.
No M0/M1/M3 biological model is fitted.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib
from collections import defaultdict
from datetime import datetime, timezone

from scripts.neobat_gbif_metadata_preflight import read_source, COMMIT
from scripts.neobat_same_cell_source_support import links_from_author_tables
from scripts.neobat_summarize_full_source_qc import EXPECTED

QC="docs/replication/neobat/gbif_full_source_qc.json"
ROSTER="docs/replication/neobat/NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json"
EMBARGO="docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json"
SOURCE_TRAINABILITY="docs/replication/neobat/plant_crossfit_source_trainability.json"
DESIGN="docs/replication/NEOBAT_V2_106PLANT_EXPLORATORY_SOURCE_GATE_FROZEN_20261119.md"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def strict_cells(q):
    groups=q.get("groups",{})
    if q.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise ValueError("NO_FULL_DOI_SOURCE_QC")
    out={}
    for group in ("bat","plant"):
        d=groups[group];e=EXPECTED[group]
        if (d["DOI"]!=e["doi"] or d["source_archive_sha256"]!=e["archive_sha"] or
            d["full_archive_rows_checked"]!=e["n_records"]):
            raise ValueError("DOI_SHA_RECORDS_MISMATCH_"+group)
        out[group]={
            "names":{r["taxon"] for r in d["species_summary"]},
            "country":{(r["taxon"],r["country"]):r["precision_le12500m_25km_cells"]
                       for r in d["species_country_summary"]}
        }
    if len(out["bat"]["names"])!=26 or len(out["plant"]["names"])!=255:
        raise ValueError("COHORT_TAXA_DRIFT")
    return out


def fixed_trainable_species(plant_cells,plant_names,countries):
    total=defaultdict(int)
    for (plant,_),n in plant_cells.items():
        if n<0:raise ValueError("NEGATIVE_PLANT_CELLS")
        total[plant]+=n
    # No bat outcomes, source cooccurrences or network references participate
    # in selecting the global v2 plant universe.
    selected=sorted(name for name in plant_names if all(
        total[name]-plant_cells.get((name,country),0)>=20 for country in countries))
    if len(selected)!=106:
        raise ValueError("GLOBALLY_TRAINABLE_106_DENOMINATOR_STOP")
    fingerprint=hashlib.sha256(("\n".join(selected)+"\n").encode("utf-8")).hexdigest()
    return selected,fingerprint


def focal_two_edge_swap_possible(focal,edges):
    """Return True iff one legal bipartite two-edge swap changes focal diet."""
    e=set(edges)
    focal_links=[p for b,p in e if b==focal]
    for p in focal_links:
        for other,q in e:
            if other!=focal and q!=p and (focal,q) not in e and (other,p) not in e:
                return True
    return False


def inspect(q,roster,embargo,source_trainability,records,sites):
    source=strict_cells(q)
    if (roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION" or
        roster.get("total_strict_candidate_combinations")!=84):
        raise ValueError("ORIGINAL_84_ROSTER_MISMATCH")
    allpairs=roster.get("strict_84_candidate_folds",[])
    if len(allpairs)!=84 or len(set((r["bat"],r["holdout_country"]) for r in allpairs))!=84:
        raise ValueError("DUPLICATE_OR_MISSING_FROZEN_FOLDS")
    countries=sorted({r["holdout_country"] for r in allpairs})
    if len(countries)!=17:raise ValueError("COUNTRY_HOLDOUT_ROSTER_CHANGED")
    if embargo.get("status")!="FULL_ORIGINAL_SITES_REFERENCE_EMBARGO_FROZEN" or \
       embargo.get("original_site_rows")!=200:
        raise ValueError("NO_COMPLETE_AUTHOR_SITE_EMBARGO")
    if (source_trainability.get("status")!="FROZEN_DOI_PLANT_CROSSFIT_SOURCE_TRAINABILITY_ONLY" or
        source_trainability["strict_20cell_globally_trainable_in_all_17_holdouts"]!=106):
        raise ValueError("PREFIT_SOURCE_TRAINABILITY_NOT_LOCKED")
    selected,digest=fixed_trainable_species(
        source["plant"]["country"],source["plant"]["names"],countries)
    links=links_from_author_tables(
        records,sites,bats=source["bat"]["names"],plants=source["plant"]["names"])
    embargo_by_country=embargo["source_reference_embargo_by_holdout"]
    selected_set=set(selected)
    rows=[]
    for r in allpairs:
        bat,country=r["bat"],r["holdout_country"]
        banned=set(embargo_by_country[country])
        # Full holdout-country site citation embargo is applied to all
        # original NeoBat literature links, including outcountry sites.
        train=[(b,plant,ref) for b,plant,ref,origin in links
               if origin!=country and ref not in banned and plant in selected_set]
        # Same-country observed plant presence threshold as frozen v1,
        # *not* proof of resource supply at any one bat observation.
        partners=sorted({p for b,p,ref in train if b==bat and
                         source["plant"]["country"].get((p,country),0)>=5})
        refs={ref for b,p,ref in train if b==bat and p in partners}
        eligible=len(partners)>=3 and len(refs)>=2
        network_edges={(b,p) for b,p,ref in train}
        focal_possible=focal_two_edge_swap_possible(bat,network_edges) if eligible else False
        rows.append({
            "bat":bat,
            "holdout_country":country,
            "original_v1_source_candidate":True,
            "v2_106_plant_source_partners":len(partners),
            "v2_106_plant_source_refs":len(refs),
            "v2_106_plant_input_qualified":eligible,
            "v2_106_plant_N1_focal_twoedge_swap_possible":focal_possible,
            "no_bat_response_or_AUC_inspected":True
        })
    return {
        "schema_version":1,
        "status":"SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "design":DESIGN,
        "original_v1_roster_size":84,
        "original_author_commit":COMMIT,
        "bat_DOI":EXPECTED["bat"]["doi"],
        "plant_DOI":EXPECTED["plant"]["doi"],
        "v2_fixed_plant_species_count":len(selected),
        "v2_fixed_plant_universe_sha256":digest,
        "v2_fixed_plant_names":selected,
        "v2_input_qualified_fold_count":sum(x["v2_106_plant_input_qualified"] for x in rows),
        "v2_not_qualified_fold_count":sum(not x["v2_106_plant_input_qualified"] for x in rows),
        "v2_input_qualified_with_N1_focal_swap":sum(
            x["v2_106_plant_input_qualified"] and
            x["v2_106_plant_N1_focal_twoedge_swap_possible"] for x in rows),
        "original_84_all_accounted":True,
        "original_255_plant_v1_contract_unmodified":True,
        "heldout_bat_occurrence_scores_opened":False,
        "same_cell_outcome_used_for_selection":False,
        "M3_minus_M1_auc":None,
        "M3_minus_N1_auc":None,
        "biological_hypothesis_tested":False,
        "folds":rows
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/replication/neobat/v2_106plant_reference_input_gate.json")
    a=p.parse_args();dest=pathlib.Path(a.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        tbl={}
        for name in ("records","sites"):
            tbl[name],_=read_source(name)
        result=inspect(read(QC),read(ROSTER),read(EMBARGO),read(SOURCE_TRAINABILITY),
                       tbl["records"],tbl["sites"])
    except Exception as exc:
        result={
            "schema_version":1,
            "status":"V2_106_PLANT_SOURCE_GATE_STOP",
            "error_type":type(exc).__name__,
            "error_code":str(exc)[:200],
            "M3_minus_M1_auc":None,"M3_minus_N1_auc":None
        }
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("V2_106_PLANT_SOURCE_GATE",result["status"],flush=True)
    if "v2_input_qualified_fold_count" in result:
        print("V2_QUALIFIED",result["v2_input_qualified_fold_count"],
              "N1_FOCAL_SWAPPABLE",result["v2_input_qualified_with_N1_focal_swap"],flush=True)
    return 0 if result["status"]=="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY" else 3


if __name__=="__main__":
    raise SystemExit(main())
