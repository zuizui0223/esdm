"""NeoBat: strict 25km bat target-group background source feasibility.

Original DOI-backed occurrence record archive is re-streamed, validated
against its source-verified full QC. No raw coordinates, source ID or cell
identifier leaves process memory. No ecological rank model is evaluated.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import tempfile
from collections import defaultdict
from datetime import datetime, timezone

from scripts.neobat_gbif_archive_header_preflight import verified_source, safe_archive
from scripts.neobat_gbif_full_source_qc import name_map
from scripts.neobat_same_cell_source_support import strict_cell_records, validate_against_full_qc
from scripts.neobat_summarize_full_source_qc import EXPECTED

ROOT=pathlib.Path("docs/replication")
D=ROOT/"neobat"
DESIGN=str(ROOT/"NEOBAT_BAT_TARGETGROUP_BACKGROUND_SOURCE_GATE_FROZEN_20261119.md")
FROZEN_ROSTER=D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def build_country_cells(bat_cells):
    """{country:{cell:{taxon: set(datasetKeys)}}}, in RAM only."""
    out=defaultdict(lambda: defaultdict(dict))
    for (bat,country),mapping in bat_cells.items():
        for cell,datasets in mapping.items():
            if bat in out[country][cell]:
                raise RuntimeError("DUPLICATE_BAT_CELL_IN_INDEX")
            out[country][cell][bat]=set(datasets)
    return out


def candidate_cells(country_cells,bat,country):
    source=country_cells.get(country,{})
    positive={}
    backgrounds={}
    for cell,observations in source.items():
        if bat in observations:
            positive[cell]=observations[bat]
        else:
            others=set().union(*observations.values()) if observations else set()
            if others:
                backgrounds[cell]=others
    return positive,backgrounds


def count_fold(country_cells,bat,holdout,countries):
    if holdout not in countries:raise ValueError("HELDOUT_NOT_IN_FIXED_COUNTRIES")
    ptest,btest=candidate_cells(country_cells,bat,holdout)
    train_presence=0
    train_background=0
    train_matched=0
    train_countries_with_positive=0
    train_countries_with_bg=0
    for country in countries:
        if country==holdout:continue
        pos,bg=candidate_cells(country_cells,bat,country)
        train_presence+=len(pos)
        train_background+=len(bg)
        if pos:train_countries_with_positive+=1
        if bg:train_countries_with_bg+=1
        source_dataset_keys={s for values in pos.values() for s in values if s}
        train_matched+=sum(bool(source_dataset_keys.intersection(
            k for k in datasets if k)) for datasets in bg.values())
    test_dataset_keys={s for values in ptest.values() for s in values if s}
    test_matched=sum(bool(test_dataset_keys.intersection(
        k for k in datasets if k)) for datasets in btest.values())
    matched=ptest and len(ptest)>=5 and len(btest)>=5 and train_presence>=20 and train_background>=20
    status="SOURCE_TARGETGROUP_BACKGROUND_QUANTITY_QUALIFIED" if matched else "SOURCE_BACKGROUND_DENOMINATOR_STOP"
    return {
       "bat":bat,"holdout_country":holdout,
       "test_focal_recorded_cells":len(ptest),
       "test_other_bat_background_cells":len(btest),
       "test_bg_cells_sharing_focal_datasetKey_in_country":test_matched,
       "train_focal_recorded_cells":train_presence,
       "train_other_bat_background_cells":train_background,
       "train_bg_cells_sharing_focal_datasetKey_within_country":train_matched,
       "train_countries_with_focal_recorded_cells":train_countries_with_positive,
       "train_countries_with_other_bat_background_cells":train_countries_with_bg,
       "quantity_qualified":bool(matched),
       "stricter_same_dataset_quantity_diagnostic":bool(matched and test_matched>=5 and train_matched>=20),
       "status":status,
       "other_taxon_record_is_not_focal_species_absence":True
    }


def inspect(bat_cells,qc,roster):
    if roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION":
        raise RuntimeError("FROZEN_84_ROSTER_STATUS_MISSING")
    pairs=roster.get("strict_84_candidate_folds",[])
    if len(pairs)!=84 or len(set((x["bat"],x["holdout_country"]) for x in pairs))!=84:
        raise RuntimeError("ORIGINAL_84_PAIRS_CHANGED")
    allcountries=read(D/"NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")["GBIF_29_country_universe"]
    if len(set(allcountries))!=29:raise RuntimeError("FROZEN_COUNTRY_DENOMINATOR_DRIFT")
    validate_against_full_qc("bat",bat_cells,qc)
    country_cells=build_country_cells(bat_cells)
    out=[count_fold(country_cells,x["bat"],x["holdout_country"],allcountries) for x in pairs]
    if [(x["bat"],x["holdout_country"]) for x in out] != [
       (x["bat"],x["holdout_country"]) for x in pairs]:
        raise RuntimeError("OUTPUT_FOLD_ORDER_CHANGED")
    nready=sum(x["quantity_qualified"] for x in out)
    nsame=sum(x["stricter_same_dataset_quantity_diagnostic"] for x in out)
    summary={
        "all_original_folds":84,
        "frozen_106_plant_source_qualified":83,
        "targetgroup_quantity_qualified_folds":nready,
        "targetgroup_quantity_stopped_folds":84-nready,
        "same_dataset_stricter_quantity_qualified_folds":nsame,
        "targetgroup_quantity_qualified_and_frozen_106_source":sum(
            x["quantity_qualified"] and not (
                x["bat"]=="Sturnira tildae" and x["holdout_country"]=="CO")
            for x in out),
        "stopped_by_zero_test_targetgroup_bg":sum(
            x["test_other_bat_background_cells"]==0 for x in out),
        "stopped_by_test_targetgroup_bg_under5":sum(
            x["test_other_bat_background_cells"]<5 for x in out),
        "stopped_by_train_targetgroup_bg_under20":sum(
            x["train_other_bat_background_cells"]<20 for x in out),
        "denominator_84_kept_even_when_stop":True
    }
    return {
        "schema_version":1,
        "status":"DOI_BAT_TARGETGROUP_BACKGROUND_INPUT_FEASIBILITY_ONLY",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_design":DESIGN,
        "source_bat_DOI":EXPECTED["bat"]["doi"],
        "source_bat_archive_sha256":EXPECTED["bat"]["archive_sha"],
        "original_85k_bat_DOI_reverified":True,
        "GBIF_plant_source_or_rows_opened":False,
        "all_original_84_roster_retained":True,
        "source_exploratory_responses_previously_opened":True,
        "not_a_true_absence_or_detection_calibration":True,
        "M3_minus_M1_auc":None,
        "M3_minus_rewired_N1_auc":None,
        "summary":summary,"folds":out
    }


def execute():
    meta=read(D/"gbif_archive_header_preflight.json")
    originals=verified_source(read(D/"gbif_download_submission.json"),
                              read(D/"gbif_download_doi_poll.json"))
    if meta.get("status")!="BOTH_ARCHIVE_HEADERS_VERIFIED":
        raise RuntimeError("ARCHIVE_HEADER_ORIGINAL_NOT_VERIFIED")
    names=name_map(read(D/"gbif_search_preflight.json"),
                   read(D/"plant_search_preflight.json"))
    qc=read(D/"gbif_full_source_qc.json")
    roster=read(FROZEN_ROSTER)
    with tempfile.TemporaryDirectory(prefix="neobat-bat-bg-original-") as temp:
        path=pathlib.Path(temp)/"bat.zip"
        bat=originals["bat"]
        if bat["doi"]!=EXPECTED["bat"]["doi"] or bat["metadata_record_count"]!=EXPECTED["bat"]["n_records"]:
            raise RuntimeError("ORIGINAL_BAT_DOI_METADATA_DRIFT")
        receipt=safe_archive(bat["url"],path)
        if receipt["sha256"]!=EXPECTED["bat"]["archive_sha"] or \
           receipt["sha256"]!=meta["files"]["bat"]["sha256"]:
            raise RuntimeError("ORIGINAL_BAT_ARCHIVE_SHA_DRIFT")
        bat_cells=strict_cell_records(path,group="bat",
            source=meta["files"]["bat"],accepted=names["bat"],
            expected_count=EXPECTED["bat"]["n_records"])
        result=inspect(bat_cells,qc,roster)
    result["source_zip_actual_sha256"]=receipt["sha256"]
    result["original_raw_rows_or_coordinates_committed"]=False
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="build/neobat/bat_targetgroup_background_gate.json")
    args=parser.parse_args()
    p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    try:
        receipt=execute()
    except Exception as exc:
        receipt={
            "schema_version":1,"status":"DOI_BAT_TARGETGROUP_BACKGROUND_SOURCE_STOP",
            "error_type":type(exc).__name__,"error_code":str(exc)[:220],
            "M3_minus_M1_auc":None
        }
    p.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("NEOBAT_BAT_TARGETGROUP",receipt["status"],flush=True)
    if "summary" in receipt:
        print("NEOBAT_BACKGROUND_SUMMARY",json.dumps(receipt["summary"],sort_keys=True),flush=True)
    return 0 if receipt["status"]=="DOI_BAT_TARGETGROUP_BACKGROUND_INPUT_FEASIBILITY_ONLY" else 3


if __name__=="__main__":
    raise SystemExit(main())
