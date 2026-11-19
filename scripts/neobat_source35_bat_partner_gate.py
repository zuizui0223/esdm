"""NeoBat original 84 bat folds against globally source-disjoint 35-plant pool.

Source-only v3 exploratory input audit. Fixed 35 names derive exclusively
from *previously sealed* 1802 plant source-key embargo eligibility. Original
author NeoBat records/sites are hashed and used only for frugivory links.
No GBIF occurrence re-download, plant fit or bat AUC in this program.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
from collections import Counter
from datetime import datetime,timezone

from scripts import neobat_v2_106plant_reference_gate as v2
from scripts.neobat_gbif_metadata_preflight import read_source,COMMIT
from scripts.neobat_same_cell_source_support import links_from_author_tables
from scripts.neobat_summarize_full_source_qc import EXPECTED
from scripts.neobat_plant_global_dataset_embargo_gate import PASS_STATUS as SOURCE_STATUS

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_35_GLOBALLY_SOURCE_DISJOINT_PARTNER_GATE_FROZEN_20261119.md"
PASS="EXPLORATORY_FIXED35_BAT_FRUITLINK_SOURCE_AND_N1_FEASIBILITY_ONLY"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def global_disjoint_names(gate,plant_names,holdouts,expected=35):
    if gate.get("status")!=SOURCE_STATUS or \
       gate.get("summary",{}).get("original_1802_denominator_intact") is not True:
        raise ValueError("ORIGINAL_1802_DISJOINT_SOURCE_GATE_NOT_VERIFIED")
    entries=gate.get("plant_country_input_gates")
    if not isinstance(entries,list) or len(entries)!=1802:
        raise ValueError("SOURCE_1802_ROWS_INCOMPLETE")
    seen={}
    for r in entries:
        key=(r["plant"],r["holdout_country"])
        if key in seen:
            raise ValueError("DUPLICATE_1802_PLANT_COUNTRY_ROW")
        seen[key]=bool(r["train_quantity_eligible_after_global_dataset_embargo"])
    if set(seen)!={(p,c) for p in plant_names for c in holdouts}:
        raise ValueError("FROZEN_106_BY17_SOURCE_GRID_CHANGED")
    names=sorted(p for p in plant_names if all(seen[p,c] for c in holdouts))
    if len(names)!=expected or gate["summary"].get(
       "source_disjoint_trainable_plant_species_all_17_holdouts")!=expected:
        raise ValueError("SOURCE_DISJOINT_35_GLOBAL_PLANT_NUMBER_DRIFT")
    digest=hashlib.sha256(("\n".join(names)+"\n").encode()).hexdigest()
    return names,digest


def quantify(source,qc,roster,site_embargo,previous106,background,raster,
             records,sites):
    if roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION":
        raise ValueError("ORIGINAL_84_BAT_ROSTER_NOT_FROZEN")
    batfolds=roster.get("strict_84_candidate_folds",[])
    if len(batfolds)!=84 or len({(x["bat"],x["holdout_country"])
                                 for x in batfolds})!=84:
        raise ValueError("ORIGINAL_84_BAT_FOLD_KEYS_DRIFT")
    if previous106.get("status")!="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY" or \
       previous106.get("v2_fixed_plant_species_count")!=106:
        raise ValueError("PRIOR_106_FRUITLINK_GATE_NOT_VERIFIED")
    if background.get("status")!="DOI_BAT_TARGETGROUP_BACKGROUND_INPUT_FEASIBILITY_ONLY" or \
       len(background.get("folds",[]))!=84:
        raise ValueError("PRIOR_BAT_TARGETGROUP_GATE_NOT_VERIFIED")
    if raster.get("status")!="FIXED106_PLANT_TRAINING_AFTER_RASTER_PREFIT_GATE" or \
       len(raster.get("per_country",[]))!=17:
        raise ValueError("ORIGINAL_FULL106_RASTER_GATE_NOT_VERIFIED")
    if site_embargo.get("status")!="FULL_ORIGINAL_SITES_REFERENCE_EMBARGO_FROZEN" or \
       site_embargo["original_site_rows"]!=200:
        raise ValueError("ORIGINAL_AUTHOR_COMPLETE_SITE_REFERENCE_EMBARGO_INVALID")
    originally=v2.strict_cells(qc)
    oldplant=previous106["v2_fixed_plant_names"]
    if sorted(set(oldplant))!=oldplant or len(oldplant)!=106 or \
       hashlib.sha256(("\n".join(oldplant)+"\n").encode()).hexdigest()!= \
       previous106["v2_fixed_plant_universe_sha256"]:
        raise ValueError("ORIGINAL_106_PLANT_SOURCE_HASH_CHANGED")
    countries=sorted({r["holdout_country"] for r in batfolds})
    if len(countries)!=17:
        raise ValueError("FROZEN_17_ORIGINAL_COUNTRIES_CHANGED")
    selected,digest=global_disjoint_names(source,oldplant,countries)
    included=set(selected)
    partner_links=links_from_author_tables(
        records,sites,bats=originally["bat"]["names"],
        plants=originally["plant"]["names"])
    prior106_map={(x["bat"],x["holdout_country"]):x
                  for x in previous106["folds"]}
    batbg_map={(x["bat"],x["holdout_country"]):x for x in background["folds"]}
    if len(prior106_map)!=84 or len(batbg_map)!=84:
        raise ValueError("PRIOR_BAT_FOLD_KEYS_NOT_UNIQUE")
    banned_by_country=site_embargo["source_reference_embargo_by_holdout"]
    allrows=[]
    for row in batfolds:
        bat,country=row["bat"],row["holdout_country"]
        banned=set(banned_by_country[country])
        eligible_links=[(s,p,ref) for s,p,ref,origin in partner_links
                        if origin!=country and ref not in banned and p in included]
        partners={p for s,p,ref in eligible_links if s==bat and
                  originally["plant"]["country"].get((p,country),0)>=5}
        refs={ref for s,p,ref in eligible_links if s==bat and p in partners}
        literature=len(partners)>=3 and len(refs)>=2
        edges={(s,p) for s,p,ref in eligible_links}
        swappable=v2.focal_two_edge_swap_possible(bat,edges) if literature else False
        old=prior106_map[bat,country]
        if literature and not old["v2_106_plant_input_qualified"]:
            raise RuntimeError("SOURCE35_CANNOT_REGAIN_UNQUALIFIED_106_LINKS")
        bg=batbg_map[bat,country]["quantity_qualified"]
        allrows.append({
            "bat":bat,"holdout_country":country,
            "frozen_original_84_pair":True,
            "previous_106_partner_input_qualified":bool(old["v2_106_plant_input_qualified"]),
            "previous_26bat_targetgroup_bg_quantity_qualified":bool(bg),
            "selected_35_actual_NeoBat_partner_species_with_5plus_local_cells":len(partners),
            "selected_35_outcountry_original_NeoBat_pub_references":len(refs),
            "selected_35_published_link_source_qualified":bool(literature),
            "selected_35_focal_degree_preserving_two_edge_swap_possible":bool(swappable),
            "selected_35_joint_bat_background_and_link_N1_source_qualified":
                bool(literature and swappable and bg),
            "source_recorded_partner_not_actual_feeding":True,
            "full_35_post_dataset_raster_trainability_not_yet_tested":True,
            "bat_M3_minus_M1_auc":None
        })
    if len(allrows)!=84 or [(r["bat"],r["holdout_country"]) for r in allrows]!=[
       (r["bat"],r["holdout_country"]) for r in batfolds]:
        raise ValueError("ALL_ORIGINAL_84_BAT_FOLDS_NOT_ACCOUNTED")
    untrainable_106={c["country"]:set(c["untrainable_plant_names"])
                     for c in raster["per_country"]}
    # Original raster screen was computed with nonembargoed source datasets.
    # Its intersection is only an *upper bound* on jointly eligible
    # source-disjoint and raster-valid training, not a fitted model.
    original_raster_upper={c:len(included-untrainable_106[c])
                           for c in countries}
    if any(n>35 for n in original_raster_upper.values()):
        raise RuntimeError("UPPER_BOUND_BROKEN")
    counts=Counter(x["holdout_country"] for x in allrows if x[
        "selected_35_joint_bat_background_and_link_N1_source_qualified"])
    summary={
        "original_bat_country_denominator":84,
        "fixed_global_source_disjoint_plants":35,
        "original_17_holdout_countries":17,
        "source35_literature_3plant_2refs_qualified_folds":sum(
            r["selected_35_published_link_source_qualified"] for r in allrows),
        "source35_literature_and_N1_focal_swap_qualified_folds":sum(
            r["selected_35_published_link_source_qualified"] and
            r["selected_35_focal_degree_preserving_two_edge_swap_possible"]
            for r in allrows),
        "source35_literature_and_N1_and_bat_bg_qualified_folds":sum(
            r["selected_35_joint_bat_background_and_link_N1_source_qualified"]
            for r in allrows),
        "distinct_bats_in_joint_source_candidate_folds":len({
            r["bat"] for r in allrows if r[
                "selected_35_joint_bat_background_and_link_N1_source_qualified"]}),
        "distinct_countries_in_joint_source_candidate_folds":len(counts),
        "per_country_joint_source_candidates":dict(sorted(counts.items())),
        "full35_unembargoed_raster_trainable_original_upper_bound_by_country":
            dict(sorted(original_raster_upper.items())),
        "source_and_raster_jointly_trainable_not_computed":True,
        "all_original_84_retained":True
    }
    return {
        "schema_version":1,
        "status":PASS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "original_author_commit":COMMIT,
        "plant_DOI":EXPECTED["plant"]["doi"],
        "bat_DOI":EXPECTED["bat"]["doi"],
        "original_106_plant_universe_sha256":
            previous106["v2_fixed_plant_universe_sha256"],
        "source35_fixed_plant_names":selected,
        "source35_fixed_plant_names_sha256":digest,
        "selected_on_input_quantity_not_bat_AUC_or_literature_links":True,
        "source_only_no_plant_or_bat_SDMS_fitted":True,
        "source_dataset_disjoint_not_survey_independent":True,
        "no_raw_GBIF_locations_or_sourceIDs_saved":True,
        "M3_minus_M1_bat_auc":None,
        "M3_minus_N1_bat_auc":None,
        "summary":summary,
        "original_84_bat_country_folds":allrows
    }


def execute():
    q=read(D/"gbif_full_source_qc.json")
    roster=read(D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json")
    embargo=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")
    previous=read(D/"v2_106plant_reference_input_gate.json")
    batbg=read(D/"bat_targetgroup_background_gate.json")
    raster=read(D/"full106_raster_trainability_gate.json")
    source=read(D/"plant_106x17_global_source_embargo.json")
    tables={}
    for name in ("records","sites"):
        tables[name],_=read_source(name)
    return quantify(source,q,roster,embargo,previous,batbg,raster,
                    tables["records"],tables["sites"])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="docs/replication/neobat/source35_bat_literature_N1_input_gate.json")
    a=parser.parse_args()
    out=pathlib.Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    try:result=execute()
    except Exception as exc:
        result={"schema_version":1,
                "status":"SOURCE35_BAT_FRUITLINK_AND_N1_INPUT_GATE_STOP",
                "error_type":type(exc).__name__,"error_code":str(exc)[:200],
                "M3_minus_M1_bat_auc":None}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_FIXED35_LINK_N1",result["status"],flush=True)
    if "summary" in result:
        print("SOURCE35_LINK_GATE_COUNTS",json.dumps({
           k:v for k,v in result["summary"].items()
           if k not in ("full35_unembargoed_raster_trainable_original_upper_bound_by_country",
                        "per_country_joint_source_candidates")
        },sort_keys=True),flush=True)
    return 0 if result["status"]==PASS else 3


if __name__=="__main__":
    raise SystemExit(main())
