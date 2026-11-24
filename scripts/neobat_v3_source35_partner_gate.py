"""NeoBat v3 global source-disjoint 35-plant *input* partner/N1 gate.

Read original, source-verified aggregate 106x17 plant training-cell quantities;
derive a single globally trainable intersection WITHOUT using AUCs. Re-test
all 84 frozen bat-country source-literature folds and original ref embargo.
No plant or bat occurrence rows, ecological fits, source IDs, cell IDs saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone

from scripts.neobat_v2_106plant_reference_gate import (
    read,strict_cells,focal_two_edge_swap_possible
)
from scripts.neobat_gbif_metadata_preflight import read_source,COMMIT
from scripts.neobat_same_cell_source_support import links_from_author_tables
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_V3_SOURCE35_PARTNER_FEASIBILITY_FROZEN_20261119.md"
V2_HASH="41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
GLOBAL_SOURCE_STATUS="EXPLORATORY_BOTANICAL_GLOBAL_DATASETKEY_EMBARGO_FEASIBILITY_ONLY"
SUCCESS="EXPLORATORY_V3_SOURCE_DISJOINT_35PLANT_FRUIT_PARTNER_GATE"
SOURCE_COUNT=35
N_PAIRS=84


def fixed_source35(v2,global_source,roster):
    """Return globally source-trainable intersection, *not* habitat-selected."""
    if (v2.get("status")!="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY"
        or v2.get("v2_fixed_plant_universe_sha256")!=V2_HASH):
        raise RuntimeError("FIXED_106_PLANT_SOURCE_INPUT_IDENTITY_DRIFT")
    plants=v2["v2_fixed_plant_names"]
    if (len(plants)!=106 or sorted(set(plants))!=plants or
        hashlib.sha256(("\n".join(plants)+"\n").encode()).hexdigest()!=V2_HASH):
        raise RuntimeError("FIXED_106_NAMES_OR_HASH_DRIFT")
    if (roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION"
        or len(roster.get("strict_84_candidate_folds",[]))!=N_PAIRS):
        raise RuntimeError("FROZEN_84_BAT_COUNTRY_ROSTER_DRIFT")
    holdouts=sorted({x["holdout_country"] for x in roster["strict_84_candidate_folds"]})
    if len(holdouts)!=17:
        raise RuntimeError("FROZEN_17_COUNTRY_DENOMINATOR_CHANGED")
    if (global_source.get("status")!=GLOBAL_SOURCE_STATUS
        or global_source.get("original_plant_country_pairs")!=1802
        or global_source.get("summary",{}).get("source_disjoint_trainable_plant_species_all_17_holdouts")!=SOURCE_COUNT):
        raise RuntimeError("ALL_SOURCE_DATASET_EMBARGO_EVIDENCE_DRIFT")
    pairs=global_source.get("plant_country_input_gates")
    if not isinstance(pairs,list) or len(pairs)!=1802:
        raise RuntimeError("FROZEN_1802_GLOBAL_SOURCE_CELL_ROWS_REQUIRED")
    bykey={(x["plant"],x["holdout_country"]):x for x in pairs}
    if len(bykey)!=1802 or set(bykey)!={(p,c) for p in plants for c in holdouts}:
        raise RuntimeError("FROZEN_1802_GLOBAL_SOURCE_PAIR_KEYS_CHANGED")
    trainable=set()
    for name in plants:
        if all(bykey[name,c].get("train_quantity_eligible_after_global_dataset_embargo") is True
               and bykey[name,c]["train_focal_recorded_cells_disjoint_datasets"]>=20
               and bykey[name,c]["train_background_cells_disjoint_datasets"]>=20
               for c in holdouts):
            trainable.add(name)
    sorted_names=sorted(trainable)
    if len(sorted_names)!=SOURCE_COUNT:
        raise RuntimeError("GLOBAL_SOURCE35_INTERSECTION_COUNT_CHANGED")
    digest=hashlib.sha256(("\n".join(sorted_names)+"\n").encode()).hexdigest()
    return sorted_names,digest,holdouts


def source_partner_gate(qc,roster,study_embargo,links,source35,batbg,raster):
    cohort=strict_cells(qc)
    if (len(cohort["bat"]["names"])!=26 or len(cohort["plant"]["names"])!=255 or
        not set(source35).issubset(cohort["plant"]["names"])):
        raise RuntimeError("ORIGINAL_DOI_26_BAT_255_PLANT_COHORT_STOP")
    if (study_embargo.get("status")!="FULL_ORIGINAL_SITES_REFERENCE_EMBARGO_FROZEN" or
        study_embargo.get("original_site_rows")!=200 or
        study_embargo.get("distinct_original_publication_references")!=169):
        raise RuntimeError("ORIGINAL_COMPLETE_NEO_STUDY_REFERENCE_EMBARGO_CHANGED")
    batbg_rows=batbg.get("folds")
    raster_rows=raster.get("all_original_84_bat_folds")
    if not isinstance(batbg_rows,list) or len(batbg_rows)!=84 or not isinstance(raster_rows,list) or len(raster_rows)!=84:
        raise RuntimeError("BAT_BACKGROUND_OR_RASTER_SOURCE_84_EVIDENCE_MISSING")
    bg_map={(r["bat"],r["holdout_country"]):r for r in batbg_rows}
    raster_map={(r["bat"],r["holdout_country"]):r for r in raster_rows}
    v2_map={(r["bat"],r["holdout_country"]):r for r in
            read(D/"v2_106plant_reference_input_gate.json")["folds"]}
    rosterpairs=[(r["bat"],r["holdout_country"]) for r in roster["strict_84_candidate_folds"]]
    if (len(set(rosterpairs))!=84 or set(bg_map)!=set(rosterpairs) or
        set(raster_map)!=set(rosterpairs) or set(v2_map)!=set(rosterpairs)):
        raise RuntimeError("BAT_SOURCE_84_ROSTERS_MISMATCH")
    pool=set(source35)
    original_bats=cohort["bat"]["names"]
    true_plant_counts=cohort["plant"]["country"]
    original_links=links
    rows=[]
    for bat,country in rosterpairs:
        if bat not in original_bats:
            raise RuntimeError("BAT_CONCEPT_NOT_IN_ORIGINAL_SOURCE")
        banned=set(study_embargo["source_reference_embargo_by_holdout"][country])
        train=[(b,p,ref) for b,p,ref,source_country in original_links
               if p in pool and source_country!=country and ref not in banned]
        if any(ref in banned for _,_,ref in train):
            raise RuntimeError("PUBLICATION_EMBARGO_SOURCE_LEAK")
        locally_recorded={p for b,p,ref in train if b==bat and
                          true_plant_counts.get((p,country),0)>=5}
        refs={ref for b,p,ref in train if b==bat and p in locally_recorded}
        edges={(b,p) for b,p,ref in train}
        enough=len(locally_recorded)>=3 and len(refs)>=2
        swappable=focal_two_edge_swap_possible(bat,edges) if enough else False
        bg_pass=bg_map[bat,country]["quantity_qualified"] is True
        old_raster=raster_map[bat,country]["full_v2_source_and_plant_training_ready"] is True
        rows.append({
            "bat":bat,
            "holdout_country":country,
            "v1_original_frozen_source_candidate":True,
            "fixed_v2_106_literature_qualified":v2_map[bat,country]["v2_106_plant_input_qualified"],
            "new_source_disjoint35_documented_fruit_partners":len(locally_recorded),
            "new_source_disjoint35_distinct_NeoBat_training_refs":len(refs),
            "new_source_disjoint35_literature_qualified":enough,
            "new_source_disjoint35_focal_N1_twoedge_swap_possible":swappable,
            "bat_original_source_targetgroup_background_qualified":bg_pass,
            "prior_full106_raster_quantity_qualified":old_raster,
            "new35_and_bat_source_quantity_qualified":bool(enough and swappable and bg_pass),
            "new35_and_prior106_raster_qualified_diagnostic_only":bool(enough and swappable and bg_pass and old_raster),
            "source_disjoint35_raster_trainability_not_yet_checked":True,
            "real_M3_minus_M1_bat_auc":None
        })
    return rows


def execute():
    qc=read(D/"gbif_full_source_qc.json")
    roster=read(D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json")
    full=read(D/"plant_106x17_global_source_embargo.json")
    v2=read(D/"v2_106plant_reference_input_gate.json")
    study=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")
    bg=read(D/"bat_targetgroup_background_gate.json")
    raster=read(D/"full106_raster_trainability_gate.json")
    names,sha,countries=fixed_source35(v2,full,roster)
    tables={}
    for key in ("records","sites"):
        tables[key],_=read_source(key)
    if len(tables["sites"])!=200:
        raise RuntimeError("ORIGINAL_200_NEO_STUDY_SITES_CHANGED")
    source=strict_cells(qc)
    links=links_from_author_tables(
        tables["records"],tables["sites"],
        bats=source["bat"]["names"],plants=source["plant"]["names"])
    rows=source_partner_gate(qc,roster,study,links,names,bg,raster)
    result={
        "schema_version":1,
        "status":SUCCESS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "design":DESIGN,
        "original_255_plant_v1_inference_unchanged":True,
        "exploratory_v2_fixed106_inference_unmodified":True,
        "fixed_106_plant_SHA":V2_HASH,
        "source_disjoint_global35_plant_names":names,
        "source_disjoint_global35_names_sha256":sha,
        "source_disjoint_global35_species_count":len(names),
        "original_country_holdouts":countries,
        "original_84_bat_folds_preserved":True,
        "original_NeoBat_source_commit":COMMIT,
        "original_bat_GBIF_DOI":EXPECTED["bat"]["doi"],
        "original_plant_GBIF_DOI":EXPECTED["plant"]["doi"],
        "no_original_GBIF_rows_coordinates_datasetKeys_or_source_refs_saved":True,
        "no_bat_or_plant_SDM_fitted":True,
        "M3_minus_M1_bat_auc":None,
        "M3_minus_N1_bat_auc":None,
        "summary":{
            "original_bat_country_folds":len(rows),
            "global_source_disjoint35_plant_species":len(names),
            "literature_partner_3plant_2ref_qualified_folds":sum(x["new_source_disjoint35_literature_qualified"] for x in rows),
            "qualified_and_focal_N1_structurally_swappable":sum(x["new_source_disjoint35_literature_qualified"] and x["new_source_disjoint35_focal_N1_twoedge_swap_possible"] for x in rows),
            "qualified_with_bat_targetgroup_source_quantity":sum(x["new35_and_bat_source_quantity_qualified"] for x in rows),
            "qualified_and_prior_full106_raster_diagnostic_only":sum(x["new35_and_prior106_raster_qualified_diagnostic_only"] for x in rows),
            "prior_106_plant_input_qualified_folds":sum(x["fixed_v2_106_literature_qualified"] for x in rows),
            "old_full106_raster_source_quantity_qualified_folds":sum(x["prior_full106_raster_quantity_qualified"] for x in rows),
            "source_disjoint35_raster_geometry_and_model_not_checked":True
        },
        "original_84_folds":rows
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="docs/replication/neobat/v3_source_disjoint35_partner_gate.json")
    args=p.parse_args()
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    try:receipt=execute()
    except Exception as exc:
        receipt={
            "schema_version":1,"status":"V3_GLOBAL_SOURCE35_PARTNER_GATE_STOP",
            "error_type":type(exc).__name__,"error_code":str(exc)[:220],
            "M3_minus_M1_bat_auc":None,"M3_minus_N1_bat_auc":None
        }
    dest.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("NEOBAT_V3_SOURCE35_FRUIT_PARTNER",receipt["status"],flush=True)
    if "summary" in receipt:
        print("SOURCE35_SUMMARY",json.dumps(receipt["summary"],sort_keys=True),flush=True)
    return 0 if receipt["status"]==SUCCESS else 3


if __name__=="__main__":
    raise SystemExit(main())
