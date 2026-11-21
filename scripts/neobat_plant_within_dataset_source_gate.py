"""NeoBat 106×17 original GBIF plant within-datasetKey source matching gate.

Pure source-input feasibility. No environmental model, plant prediction,
bat response, absence or ecological effect. Aggregate cells only; never
export original cell IDs, datasetKeys, GBIF records, or exact coordinates.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,tempfile
from collections import defaultdict
from datetime import datetime,timezone

from scripts.neobat_gbif_archive_header_preflight import verified_source,safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records,validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

D=pathlib.Path("docs/replication/neobat")
DESIGN="docs/replication/NEOBAT_PLANT_WITHIN_DATASETKEY_SOURCE_GATE_FROZEN_20261119.md"
FROZEN_V2_SHA="41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
PILOT_SENTINELS=("Cecropia obtusifolia","Ficus insipida","Piper aduncum")
PTEST_MIN,BTEST_MIN,PTRAIN_MIN,BTRAIN_MIN=5,5,20,20


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def fixed_names_and_countries():
    v2=read(D/"v2_106plant_reference_input_gate.json")
    if v2["status"]!="SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY":
        raise RuntimeError("FROZEN_106_SOURCE_STATUS_INVALID")
    names=v2["v2_fixed_plant_names"]
    if len(names)!=106 or sorted(set(names))!=names or \
       hashlib.sha256(("\n".join(names)+"\n").encode()).hexdigest()!=FROZEN_V2_SHA or \
       v2["v2_fixed_plant_universe_sha256"]!=FROZEN_V2_SHA:
        raise RuntimeError("FROZEN_106_PLANT_NAMES_CHANGED")
    roster=read(D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json")
    if roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION" or \
       len(roster.get("strict_84_candidate_folds",[]))!=84:
        raise RuntimeError("FROZEN_84_BAT_FOLDS_CHANGED")
    countries=sorted({r["holdout_country"] for r in roster["strict_84_candidate_folds"]})
    if len(countries)!=17 or "CO" not in countries:
        raise RuntimeError("FROZEN_17_COUNTRY_HOLDOUTS_CHANGED")
    return names,countries


def country_dataset_cells(plant_cells):
    """In-process mapping country -> datasetKey -> cell -> set(plants)."""
    out=defaultdict(lambda:defaultdict(lambda:defaultdict(set)))
    for (plant,country),mapping in plant_cells.items():
        for cell,dataset_ids in mapping.items():
            for key in dataset_ids:
                if key:
                    out[country][key][cell].add(plant)
    return out


def source_matched_country(plant,country,plant_cells,per_dataset):
    """Pair source-qualified focal/other-plant cells within original datasetKey.

    A matching dataset is a study collection, not a paired biological survey.
    """
    mapping=plant_cells.get((plant,country),{})
    if not mapping:
        return set(),set(),0
    keys={key for ds in mapping.values() for key in ds if key}
    pos=set()
    bg=set()
    qualified=0
    for key in keys:
        cell_taxa=per_dataset.get(country,{}).get(key,{})
        positive_cells={cell for cell,taxa in cell_taxa.items() if plant in taxa}
        nonfocal_cells={cell for cell,taxa in cell_taxa.items()
                        if any(x!=plant for x in taxa)}
        if positive_cells and nonfocal_cells:
            pos.update(positive_cells)
            bg.update(nonfocal_cells)
            qualified+=1
    # A cell known to contain the focal plant may not be used as
    # a target background regardless of which GBIF dataset reported it.
    bg.difference_update(mapping)
    return pos,bg,qualified


def all_country_source_matches(names,plant_cells,universe):
    per_dataset=country_dataset_cells(plant_cells)
    matched={}
    for name in names:
        for country in universe:
            matched[name,country]=source_matched_country(
                name,country,plant_cells,per_dataset)
    return matched


def fold_counts(name,holdout,matched,full_country_cells,source_countries):
    if holdout not in source_countries:
        raise ValueError("COUNTRY_NOT_FROZEN")
    # Exclude all source-observed cells attributed to the heldout country
    # from other-country training, even if a coarse cell intersects a border.
    excluded=full_country_cells.get(holdout,set())
    ptest,btest,ndstest=matched.get((name,holdout),(set(),set(),0))
    nP=nB=0
    datasets_in_training_country_contexts=0
    for country in source_countries:
        if country==holdout:continue
        p,b,nd=matched.get((name,country),(set(),set(),0))
        nP+=len(p-excluded)
        nB+=len(b-excluded)
        datasets_in_training_country_contexts+=nd
    trainable=nP>=PTRAIN_MIN and nB>=BTRAIN_MIN
    testscore=len(ptest)>=PTEST_MIN and len(btest)>=BTEST_MIN
    return {
        "plant":name,"holdout_country":holdout,
        "train_focal_source_matched_recorded_cells":nP,
        "train_source_matched_otherplant_bg_cells":nB,
        "test_focal_source_matched_recorded_cells":len(ptest),
        "test_source_matched_otherplant_bg_cells":len(btest),
        "test_eligible_GBIF_dataset_keys":ndstest,
        "train_eligible_dataset_country_contexts":datasets_in_training_country_contexts,
        "source_matched_training_quantity_qualified":trainable,
        "source_matched_heldout_scoring_quantity_qualified":bool(trainable and testscore),
        "holdout_test_quantity_only_qualified":testscore,
        "pseudo_background_is_not_true_absence":True,
        "datasetKey_is_not_field_event_matching":True
    }


def analyse(plant_cells,names,countries,universe):
    if len(names)!=106 or len(countries)!=17 or len(set(names))!=106:
        raise ValueError("SOURCE_GATE_FULL_106x17_REQUIRED")
    if not set(countries).issubset(universe) or len(universe)!=29:
        raise ValueError("SOURCE_GATE_COUNTRY_DENOMINATOR_CHANGED")
    matched=all_country_source_matches(names,plant_cells,universe)
    country_cells=defaultdict(set)
    for (plant,country),mapping in plant_cells.items():
        country_cells[country].update(mapping)
    rows=[fold_counts(name,country,matched,country_cells,universe)
          for name in names for country in countries]
    if len(rows)!=1802:
        raise RuntimeError("ORIGINAL_1802_PLANT_COUNTRY_DENOMINATOR_CHANGED")
    per_country=[]
    for country in countries:
        subset=[x for x in rows if x["holdout_country"]==country]
        per_country.append({
            "holdout_country":country,
            "original_plant_cohort":106,
            "source_matched_trainable_plants":sum(
                x["source_matched_training_quantity_qualified"] for x in subset),
            "source_matched_train_and_heldout_scoring_plants":sum(
                x["source_matched_heldout_scoring_quantity_qualified"] for x in subset),
            "source_matched_test_quantity_only_plants":sum(
                x["holdout_test_quantity_only_qualified"] for x in subset),
            "complete_fixed106_source_matched_training":all(
                x["source_matched_training_quantity_qualified"] for x in subset),
        })
    summary={
      "original_fixed_plant_species":106,
      "original_fixed_holdout_countries":17,
      "original_plant_country_pairs":1802,
      "source_matched_trainable_plant_country_pairs":sum(
          x["source_matched_training_quantity_qualified"] for x in rows),
      "source_matched_train_and_test_scoring_pairs":sum(
          x["source_matched_heldout_scoring_quantity_qualified"] for x in rows),
      "source_matched_trainable_plants_all_17_countries":sum(
          all(next(x["source_matched_training_quantity_qualified"] for x in rows
                   if x["plant"]==name and x["holdout_country"]==country)
              for country in countries) for name in names),
      "countries_with_full_106_source_matched_trainability":sum(
          x["complete_fixed106_source_matched_training"] for x in per_country),
      "min_trainable_per_country":min(x["source_matched_trainable_plants"] for x in per_country),
      "max_trainable_per_country":max(x["source_matched_trainable_plants"] for x in per_country),
      "all_1802_in_denominator":True,
      "none_are_plant_true_absences_or_bat_models":True,
    }
    sentinels=[x for x in rows if x["holdout_country"]=="CO" and
               x["plant"] in PILOT_SENTINELS]
    if len(sentinels)!=3:raise RuntimeError("FROZEN_PILOT_SENTINELS_NOT_PRESERVED")
    return rows,summary,per_country,sentinels


def execute():
    names,countries=fixed_names_and_countries()
    header=read(D/"gbif_archive_header_preflight.json")
    sources=verified_source(read(D/"gbif_download_submission.json"),
                            read(D/"gbif_download_doi_poll.json"))
    source_qc=read(D/"gbif_full_source_qc.json")
    accepted=name_map(read(D/"gbif_search_preflight.json"),
                      read(D/"plant_search_preflight.json"))
    universe=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")[
        "GBIF_29_country_universe"]
    if sources["plant"]["doi"]!=EXPECTED["plant"]["doi"] or \
       sources["plant"]["metadata_record_count"]!=EXPECTED["plant"]["n_records"]:
        raise RuntimeError("ORIGINAL_PLANT_DOI_OR_ROW_COUNT_DRIFT")
    with tempfile.TemporaryDirectory(prefix="neobat-plant-sourcedataset-gate-") as tmp:
        original=pathlib.Path(tmp)/"plant_original.zip"
        zipdata=safe_archive(sources["plant"]["url"],original)
        if zipdata["sha256"]!=EXPECTED["plant"]["archive_sha"] or \
           zipdata["sha256"]!=header["files"]["plant"]["sha256"]:
            raise RuntimeError("ORIGINAL_PLANT_ZIP_SHA_DRIFT")
        cells=strict_cell_records(original,group="plant",
                                 source=header["files"]["plant"],
                                 accepted=accepted["plant"],
                                 expected_count=EXPECTED["plant"]["n_records"])
        validate_against_full_qc("plant",cells,source_qc)
        rows,summary,per_country,sentinels=analyse(cells,names,countries,universe)
    return {
       "schema_version":1,
       "status":"DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY",
       "created_utc":datetime.now(timezone.utc).isoformat(),
       "frozen_design":DESIGN,
       "original_plant_DOI":EXPECTED["plant"]["doi"],
       "original_plant_archive_sha256":zipdata["sha256"],
       "source_country_and_species_counts_reproduced":True,
       "original_fixed_106_plant_universe_sha256":FROZEN_V2_SHA,
       "new_GBIF_download_POSTs":0,
       "same_GBIF_dataset_is_not_event_independence":True,
       "no_plant_or_bat_SDM_fitted":True,
       "M3_minus_M1_bat_auc":None,
       "M3_minus_N1_bat_auc":None,
       "no_original_coords_or_datasetIDs_committed":True,
       "summary":summary,
       "per_country":per_country,
       "Colombia_original_three_sentinels":sentinels,
       "plant_country_source_support":rows,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/plant_dataset_matched_106x17.json")
    p.add_argument("--compact",default="build/neobat/plant_dataset_matched_106x17_compact.json")
    args=p.parse_args()
    out=pathlib.Path(args.out); compact=pathlib.Path(args.compact)
    out.parent.mkdir(parents=True,exist_ok=True); compact.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={
           "schema_version":1,
           "status":"PLANT_106x17_WITHIN_DATASETKEY_SOURCE_STOP",
           "error_type":type(exc).__name__,
           "error_code":str(exc)[:200],
           "M3_minus_M1_bat_auc":None
        }
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    trimmed={k:v for k,v in result.items() if k!="plant_country_source_support"}
    compact.write_text(json.dumps(trimmed,indent=2,ensure_ascii=False)+"\n")
    print("NEOBAT_PLANT_WITHIN_DATASETKEY",result["status"],flush=True)
    if "summary" in result:
        print("DATASET_MATCH_SUMMARY",json.dumps(result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]=="DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY" else 3


if __name__=="__main__":
    raise SystemExit(main())
