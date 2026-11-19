"""NeoBat botanical all-source datasetKey embargo source-only feasibility.

Original 106 plant species x 17 country holdouts are fixed. Replays original
source-verified 1802 input pairs, then globally excludes every botanical
datasetKey touched by withheld country (including low precision rows) from
outcountry *training*. Emits aggregate counts only. Zero ecological fits.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import pathlib
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime,timezone

from scripts import neobat_plant_within_dataset_source_gate as previous
from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map,source_header_matches,ALLOWED_YEAR
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_BOTANICAL_GLOBAL_DATASETKEY_EMBARGO_FROZEN_20261119.md"
COLS=("train_focal_source_matched_recorded_cells",
      "train_source_matched_otherplant_bg_cells",
      "test_focal_source_matched_recorded_cells",
      "test_source_matched_otherplant_bg_cells",
      "test_eligible_GBIF_dataset_keys",
      "train_eligible_dataset_country_contexts")
SOURCE_STATUS="DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY"
STOP_STATUS="BOTANICAL_GLOBAL_DATASETKEY_SOURCE_GATE_STOP"
PASS_STATUS="EXPLORATORY_BOTANICAL_GLOBAL_DATASETKEY_EMBARGO_FEASIBILITY_ONLY"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def country_keys_from_rows(rows,expected_n):
    """All source rows with valid country/year, *regardless of precision*."""
    embargo=defaultdict(set)
    rows_total=0
    rows_year_country=0
    blank_keys=0
    country_counts=defaultdict(int)
    for row in rows:
        rows_total+=1
        try:
            year=int(row.get("year") or "")
        except (ValueError,TypeError):
            continue
        country=str(row.get("countryCode") or "").strip()
        if year not in ALLOWED_YEAR or country not in previous.read(
            D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json"
        )["GBIF_29_country_universe"]:
            continue
        rows_year_country+=1
        key=str(row.get("datasetKey") or "").strip()
        if not key:
            blank_keys+=1
            continue
        embargo[country].add(key)
        country_counts[country]+=1
    if rows_total!=expected_n:
        raise RuntimeError("ORIGINAL_PLANT_SOURCE_DATASET_KEY_ROW_DENOMINATOR_STOP")
    return embargo,{
        "original_plant_source_rows_read":rows_total,
        "original_rows_in_fixed_29_countries_year_range":rows_year_country,
        "source_rows_missing_datasetKey":blank_keys,
        "total_unique_original_dataset_keys_any_country":
            len(set().union(*embargo.values())) if embargo else 0,
        "source_dataset_country_counts":dict(sorted(
            (c,len(v)) for c,v in embargo.items())),
        "source_record_country_counts":dict(sorted(country_counts.items())),
    }


def source_embargo_from_archive(path,header,expected_n):
    with zipfile.ZipFile(path) as archive:
        entry=header["zip_entry_name"]
        if archive.namelist().count(entry)!=1:
            raise RuntimeError("ORIGINAL_PLANT_ZIP_SOURCE_MEMBER_CHANGED")
        with archive.open(entry) as file:
            reader=csv.DictReader(io.TextIOWrapper(
                file,encoding="utf-8-sig",newline=""),delimiter="\t",
                quoting=csv.QUOTE_MINIMAL)
            source_header_matches(reader.fieldnames,header["header_columns"])
            return country_keys_from_rows(reader,expected_n)


def source_matched_country_excluding(plant,country,plant_cells,per_dataset,embargo):
    """Source dataset disjoint from test; no use of cooccurrence as absence."""
    mapping=plant_cells.get((plant,country),{})
    if not mapping:return set(),set(),0
    result_pos=set()
    result_background=set()
    qualified_datasets=0
    for key in {k for vals in mapping.values() for k in vals if k}:
        if key in embargo:
            continue
        source=per_dataset.get(country,{}).get(key,{})
        pos={cell for cell,names in source.items() if plant in names}
        bg={cell for cell,names in source.items() if any(p!=plant for p in names)}
        if not pos or not bg:
            continue
        result_pos.update(pos)
        result_background.update(bg)
        qualified_datasets+=1
    # If this plant is ever known from the cell, it cannot be background.
    result_background.difference_update(mapping)
    return result_pos,result_background,qualified_datasets


def audit(original_cells,source_keys,source_summary,names,holdouts,countries,prior):
    if prior.get("status")!=SOURCE_STATUS:
        raise RuntimeError("PREVIOUS_SOURCE_1802_GATE_NOT_COMPLETE")
    old_rows=prior.get("plant_country_source_support")
    if not isinstance(old_rows,list) or len(old_rows)!=1802:
        raise RuntimeError("PRIOR_SOURCE_MATCH_FULL_1802_ROWS_REQUIRED")
    old_map={(r["plant"],r["holdout_country"]):r for r in old_rows}
    if len(old_map)!=1802:
        raise RuntimeError("PRIOR_1802_COUNTRY_SPECIES_KEYS_NOT_UNIQUE")
    indexed=previous.country_dataset_cells(original_cells)
    all_matches=previous.all_country_source_matches(names,original_cells,countries)
    full_cell_holdouts=defaultdict(set)
    for (_,country),cellmap in original_cells.items():
        full_cell_holdouts[country].update(cellmap)
    baseline_replay=0
    results=[]
    summaries=[]
    for holdout in holdouts:
        banned=source_keys.get(holdout,set())
        outside_keys={key for c,vals in source_keys.items()
                      if c!=holdout for key in vals}
        overlap=outside_keys&banned
        excluded=full_cell_holdouts[holdout]
        training_available=0
        scoring_available=0
        prior_trainable=0
        qualifying_original=0
        for plant in names:
            old=old_map.get((plant,holdout))
            if old is None:
                raise RuntimeError("PRIOR_1802_MISSING_PAIR")
            baseline=previous.fold_counts(
                plant,holdout,all_matches,full_cell_holdouts,countries)
            for key in COLS:
                if baseline[key]!=old[key]:
                    raise RuntimeError("ORIGINAL_1802_BASELINE_REPLAY_CHANGED_"+key)
            baseline_replay+=1
            prior_trainable+=int(old["source_matched_training_quantity_qualified"])
            qualifying_original+=int(old["source_matched_heldout_scoring_quantity_qualified"])
            n_positive=n_background=source_contexts=0
            for c in countries:
                if c==holdout:continue
                positive,background,nsource=source_matched_country_excluding(
                    plant,c,original_cells,indexed,banned)
                n_positive+=len(positive-excluded)
                n_background+=len(background-excluded)
                source_contexts+=nsource
            testp,testb,testk=all_matches[plant,holdout]
            train_eligible=n_positive>=20 and n_background>=20
            test_eligible=len(testp)>=5 and len(testb)>=5
            scored=bool(train_eligible and test_eligible)
            training_available+=int(train_eligible)
            scoring_available+=int(scored)
            results.append({
                "plant":plant,"holdout_country":holdout,
                "train_focal_recorded_cells_disjoint_datasets":n_positive,
                "train_background_cells_disjoint_datasets":n_background,
                "heldout_focal_recorded_cells":len(testp),
                "heldout_targetgroup_background_cells":len(testb),
                "training_source_dataset_country_contexts_after_embargo":
                    source_contexts,
                "heldout_source_dataset_context_count":testk,
                "train_quantity_eligible_after_global_dataset_embargo":train_eligible,
                "train_and_test_source_quantity_eligible_after_embargo":scored,
                "unembargoed_original_training_eligible":
                    old["source_matched_training_quantity_qualified"],
                "unembargoed_original_train_and_test_eligible":
                    old["source_matched_heldout_scoring_quantity_qualified"],
                "no_plant_true_absence_or_ecological_model":True,
            })
        summaries.append({
            "holdout_country":holdout,
            "original_fixed_plants":106,
            "source_dataset_keys_present_in_holdout_country":len(banned),
            "source_dataset_keys_shared_with_other_source_countries":len(overlap),
            "shared_fraction_of_holdout_source_dataset_keys":
                len(overlap)/len(banned) if banned else None,
            "training_quantity_qualified_before_embargo":prior_trainable,
            "training_quantity_qualified_after_embargo":training_available,
            "training_and_test_quantity_qualified_before_embargo":qualifying_original,
            "training_and_test_quantity_qualified_after_embargo":scoring_available,
            "complete_fixed106_trainable_after_embargo":training_available==106
        })
    if baseline_replay!=1802 or len(results)!=1802:
        raise RuntimeError("NOT_ALL_1802_BASELINE_AND_NEW_PAIRS_ACCOUNTED")
    original_scored=sum(x["unembargoed_original_train_and_test_eligible"] for x in results)
    after_scored=sum(x["train_and_test_source_quantity_eligible_after_embargo"]
                      for x in results)
    if original_scored!=677:
        raise RuntimeError("ORIGINAL_677_BASELINE_SOURCE_SCORING_DENOMINATOR_DRIFT")
    if sum(x["unembargoed_original_training_eligible"] for x in results)!=1802:
        raise RuntimeError("ORIGINAL_1802_TRAINABLE_DENOMINATOR_DRIFT")
    rowlookup={(r["plant"],r["holdout_country"]):r for r in results}
    sentinels=[rowlookup[p,"CO"] for p in previous.PILOT_SENTINELS]
    return {
        "schema_version":1,
        "status":PASS_STATUS,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "source_plant_GBIF_DOI":EXPECTED["plant"]["doi"],
        "source_plant_original_zip_sha256":EXPECTED["plant"]["archive_sha"],
        "original_106_plant_universe_sha256":previous.FROZEN_V2_SHA,
        "number_of_original_holdouts":17,
        "original_plant_country_pairs":1802,
        "all_original_1802_source_input_rows_exact_replay":True,
        "source_dataset_identifiers_used_in_memory_only":True,
        "bat_model_AUC_M3_minus_M1":None,
        "plant_source_AUC_after_dataset_embargo":None,
        "no_plant_models_or_bat_models_fitted":True,
        "source_dataset_disjointness_not_independent_publishers_or_sampling":True,
        "source_row_audit":source_summary,
        "summary":{
            "previous_source_quantity_trainable_pairs":1802,
            "previous_source_quantity_train_and_test_pairs":677,
            "source_disjoint_trainable_pairs":sum(
                x["train_quantity_eligible_after_global_dataset_embargo"]
                for x in results),
            "source_disjoint_train_and_test_pairs":after_scored,
            "source_disjoint_trainable_plant_species_all_17_holdouts":sum(
                all(rowlookup[p,c]["train_quantity_eligible_after_global_dataset_embargo"]
                    for c in holdouts) for p in names),
            "countries_with_all_106_source_disjoint_training":sum(
                x["complete_fixed106_trainable_after_embargo"] for x in summaries),
            "countries_with_one_or_more_scoring_candidates":sum(
                x["training_and_test_quantity_qualified_after_embargo"]>0 for x in summaries),
            "original_1802_denominator_intact":True
        },
        "per_country":summaries,
        "fixed_Colombia_3_sentinel_source_gate":sentinels,
        "plant_country_input_gates":results
    }


def execute():
    names,holdouts=previous.fixed_names_and_countries()
    original=previous.read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")
    countries=original["GBIF_29_country_universe"]
    if len(countries)!=29 or len(holdouts)!=17:
        raise RuntimeError("FROZEN_29_AND_17_COUNTRIES_REQUIRED")
    source=verified_source(read(D/"gbif_download_submission.json"),
                           read(D/"gbif_download_doi_poll.json"))
    headers=read(D/"gbif_archive_header_preflight.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    qc=read(D/"gbif_full_source_qc.json")
    prior=read(D/"plant_dataset_matched_106x17.json")
    if source["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
       source["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
        raise RuntimeError("ORIGINAL_SOURCE_DOI_OR_ROWCOUNT_CHANGED")
    with tempfile.TemporaryDirectory(prefix="neobat-source-embargo-") as directory:
        path=pathlib.Path(directory)/"plant_original.zip"
        signature=safe_archive(source["plant"]["url"],path)
        if signature["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           signature["sha256"]!=headers["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_SOURCE_ZIP_SHA_CHANGED")
        cells=strict_cell_records(
            path,group="plant",source=headers["files"]["plant"],
            accepted=accepted["plant"],expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,qc)
        country_embargo,source_summary=source_embargo_from_archive(
            path,headers["files"]["plant"],EXPECTED["plant"]["n_records"])
        result=audit(cells,country_embargo,source_summary,
                     names,holdouts,countries,prior)
    result["raw_source_coordinates_or_dataset_ids_persisted"]=False
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_106x17_global_source_embargo.json")
    p.add_argument("--compact",default="build/neobat/plant_106x17_global_source_embargo_compact.json")
    a=p.parse_args()
    dst=pathlib.Path(a.out);compact=pathlib.Path(a.compact)
    dst.parent.mkdir(parents=True,exist_ok=True);compact.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={
            "schema_version":1,"status":STOP_STATUS,
            "error_type":type(exc).__name__,"error_code":str(exc)[:220],
            "bat_model_AUC_M3_minus_M1":None,
            "plant_source_AUC_after_dataset_embargo":None
        }
    dst.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    compact.write_text(json.dumps({
        k:v for k,v in result.items() if k!="plant_country_input_gates"
    },indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_BOTANICAL_GLOBAL_DATASET_SOURCE",result["status"],flush=True)
    if "summary" in result:
        print("NEOBAT_DATASET_EMBARGO_SUMMARY",json.dumps(
            result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]==PASS_STATUS else 3


if __name__=="__main__":
    raise SystemExit(main())
