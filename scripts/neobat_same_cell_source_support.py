"""NeoBat DOI-backed strict 25km same-cell SUPPORT audit (not an SDM).

One-shot source-opening discovery stage: only species×country aggregate counts
leave memory; individual GBIF rows, coordinates, source events and cell IDs
must never be written to the Git repository or to artifacts.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

from scripts.neobat_gbif_archive_header_preflight import verified_source, safe_archive
from scripts.neobat_gbif_full_source_qc import (
    ALLOWED_YEAR, name_map, source_header_matches, REQUIRED_FIELDS
)
from scripts.neobat_spatial_cell_pilot import LATAM, label_precision, spatial_grid
from scripts.neobat_gbif_metadata_preflight import read_source, FILES, COMMIT
from scripts.neobat_resource_country_gate import COUNTRY_CODE
from scripts.neobat_summarize_full_source_qc import EXPECTED

GROUPS=("bat", "plant")
DESIGN="docs/replication/NEOBAT_SAME_CELL_INPUT_SUPPORT_FROZEN_DESIGN_20261119.md"
ROSTER="docs/replication/neobat/NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json"
EMBARGO="docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json"
QC="docs/replication/neobat/gbif_full_source_qc.json"
ARCHIVE_HEADER="docs/replication/neobat/gbif_archive_header_preflight.json"
SUBMISSION="docs/replication/neobat/gbif_download_submission.json"
POLL="docs/replication/neobat/gbif_download_doi_poll.json"
BAT_NAMES="docs/replication/neobat/gbif_search_preflight.json"
PLANT_NAMES="docs/replication/neobat/plant_search_preflight.json"


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def strict_cell_records(zip_path, *, group, source, accepted, expected_count):
    """Return only in-memory (species,country)->(25km cell->datasetKeys)."""
    cells=defaultdict(lambda: defaultdict(set))
    seen_ids=set()
    raw_count=0
    with zipfile.ZipFile(zip_path) as z:
        if z.namelist().count(source["zip_entry_name"])!=1:
            raise RuntimeError("ARCHIVE_MEMBER_NOT_UNIQUE_"+group)
        with z.open(source["zip_entry_name"]) as stream:
            reader=csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""),
                                  delimiter="\t",quoting=csv.QUOTE_MINIMAL)
            source_header_matches(reader.fieldnames,source["header_columns"])
            for row in reader:
                raw_count+=1
                if not row or any(v is None for v in row.values()):
                    continue
                key=str(row.get("speciesKey") or "")
                if key not in accepted:
                    continue
                gbif_id=str(row.get("gbifID") or "").strip()
                if gbif_id:
                    if gbif_id in seen_ids:continue
                    seen_ids.add(gbif_id)
                cc=str(row.get("countryCode") or "").strip()
                if cc not in LATAM:continue
                try:
                    year=int(row.get("year") or "")
                    latitude=float(row.get("decimalLatitude"))
                    longitude=float(row.get("decimalLongitude"))
                except (TypeError,ValueError):continue
                if year not in ALLOWED_YEAR:continue
                # The *same* EPSG:6933 grid and strict coordinate precision
                # policy as the already-frozen full DOI original source QC.
                position=spatial_grid(longitude,latitude)
                if position is None or label_precision(
                        row.get("coordinateUncertaintyInMeters"))!="known_le_12_5km":
                    continue
                cells[(accepted[key],cc)][position[0]].add(
                    str(row.get("datasetKey") or "").strip())
    if raw_count!=expected_count:
        raise RuntimeError("ORIGINAL_SOURCE_ROW_DENOMINATOR_DRIFT_"+group)
    return cells


def validate_against_full_qc(group, cells, source_qc):
    if source_qc.get("status")!="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED":
        raise RuntimeError("PINNED_FULL_DOI_QC_NOT_COMPLETE")
    original=source_qc["groups"][group]
    expect=EXPECTED[group]
    if (original["DOI"]!=expect["doi"] or
        original["source_archive_sha256"]!=expect["archive_sha"] or
        original["full_archive_rows_checked"]!=expect["n_records"]):
        raise RuntimeError("PINNED_SOURCE_IDENTITY_MISMATCH_"+group)
    expected={(r["taxon"],r["country"]):r["precision_le12500m_25km_cells"]
              for r in original["species_country_summary"]}
    for key in set(expected)|set(cells):
        if len(cells.get(key,{}))!=expected.get(key,0):
            raise RuntimeError("COUNTRY_SPECIES_STRICT_CELL_COUNT_DRIFT_"+group)
    return True


def links_from_author_tables(records, sites, *, bats, plants):
    if len(sites)!=len({s["SiteCode"] for s in sites}):
        raise RuntimeError("DUPLICATE_AUTHOR_SITE")
    bysite={s["SiteCode"]:s for s in sites}
    out=set()
    for row in records:
        if row["Interaction"]!="Frugivory" or row["TrophicGuild"]!="Frugivore":
            continue
        bat,plant=row["CurrentBatSpecies"],row["CurrentPlantSpecies"]
        if bat not in bats or plant not in plants:
            continue
        site=bysite.get(row["SiteCode"])
        if site is None or site["RefCode"]!=row["RefCode"]:
            raise RuntimeError("AUTHOR_SITE_REFERENCE_BROKEN")
        out.add((bat,plant,row["RefCode"],COUNTRY_CODE[site["Country"]]))
    if not out:raise RuntimeError("NO_VALID_SOURCE_LINKS")
    return sorted(out)


def support_counts(cells):
    """Known-precision unique cells per species, country and outside-country."""
    counts={group:{(taxon,country):len(cs) for (taxon,country),cs in cells[group].items()}
            for group in GROUPS}
    totals={group:defaultdict(int) for group in GROUPS}
    for group in GROUPS:
        for (name,_),v in counts[group].items():
            totals[group][name]+=v
    return counts,totals


def qualifying_parts(bat,country,links,counts,totals,plant_names,site_banned):
    """Mirror existing full DOI source-input gate; no response rank is touched."""
    pool={
        plant for plant in plant_names
        if counts["plant"].get((plant,country),0)>=5 and
        totals["plant"][plant]-counts["plant"].get((plant,country),0)>=20
    }
    banned=set(site_banned.get(country,[]))
    training=[(plant,ref) for b,plant,ref,source_country in links
              if b==bat and plant in pool and source_country!=country and ref not in banned]
    partners=sorted({plant for plant,ref in training})
    refs={ref for plant,ref in training if plant in partners}
    return pool,partners,refs


def roster_matches(cells,links,bats,plants,countries,site_banned,frozen_pairs):
    counts,totals=support_counts(cells)
    observed=set()
    for bat in bats:
        for country in countries:
            n=counts["bat"].get((bat,country),0)
            if n<5 or totals["bat"][bat]-n<20:continue
            pool,partners,refs=qualifying_parts(
                bat,country,links,counts,totals,plants,site_banned)
            if len(partners)>=3 and len(refs)>=2:
                observed.add((bat,country))
    if observed!=set(frozen_pairs) or len(frozen_pairs)!=84:
        raise RuntimeError("FROZEN_84_CANDIDATE_ROSTER_MISMATCH")
    return counts,totals


def different_dataset_in_same_cell(bat_sources,plant_sources):
    # Different dataset keys are only a **stronger bibliographic
    # distinction**, not proof of independent field sampling.
    a={v for v in bat_sources if v}
    p={v for v in plant_sources if v}
    return bool(a and p and (len(a|p)>1))


def one_fold(bat,country,cells,links,counts,totals,plant_names,site_banned):
    allplants,partners,refs=qualifying_parts(
        bat,country,links,counts,totals,plant_names,site_banned)
    if len(partners)<3 or len(refs)<2:
        raise RuntimeError("FROZEN_SOURCE_PARTNER_GATE_VIOLATED")
    bat_cells=cells["bat"].get((bat,country),{})
    if len(bat_cells)<5 or totals["bat"][bat]-len(bat_cells)<20:
        raise RuntimeError("FROZEN_BAT_CELL_GATE_VIOLATED")
    nonpartner=allplants-set(partners)
    metrics=defaultdict(int)
    partner_same_dataset_only=0
    for cell,bat_datasets in bat_cells.items():
        matched_partners=[
            plant for plant in partners if cell in cells["plant"].get((plant,country),{})
        ]
        matched_generic=[
            plant for plant in allplants if cell in cells["plant"].get((plant,country),{})
        ]
        if matched_partners:metrics["any_linked_partner"]+=1
        if len(matched_partners)>=3:metrics["at_least_three_linked_partners"]+=1
        if matched_generic:metrics["any_generic_plant"]+=1
        if any(p in nonpartner for p in matched_generic):
            metrics["any_nonpartner_plant"]+=1
        if any(different_dataset_in_same_cell(
                bat_datasets,cells["plant"][(p,country)][cell])
               for p in matched_partners):
            metrics["any_partner_distinct_gbif_dataset"]+=1
        if matched_partners and not any(different_dataset_in_same_cell(
                bat_datasets,cells["plant"][(p,country)][cell])
                for p in matched_partners):
            partner_same_dataset_only+=1

    return {
      "bat":bat,"holdout_country":country,
      "known_precision_bat_recorded_cells":len(bat_cells),
      "qualified_partner_species":len(partners),
      "qualified_generic_plant_species":len(allplants),
      "qualified_nonpartner_species":len(nonpartner),
      "training_original_NeoBat_refs":len(refs),
      "bat_cells_with_at_least_one_linked_plant_record":metrics["any_linked_partner"],
      "bat_cells_with_at_least_three_linked_plant_species":metrics["at_least_three_linked_partners"],
      "bat_cells_with_any_generic_plant_record":metrics["any_generic_plant"],
      "bat_cells_with_any_nonpartner_plant_record":metrics["any_nonpartner_plant"],
      "bat_cells_with_linked_plant_from_distinct_GBIF_dataset":metrics["any_partner_distinct_gbif_dataset"],
      "bat_cells_with_linked_plant_but_no_distinct_GBIF_dataset":partner_same_dataset_only,
      "zero_does_not_mean_partner_absence":True
    }


def aggregate(cells,links,roster,embargo,bat_names,plant_names):
    if roster.get("status")!="PREFIT_DISCOVERY_ELIGIBILITY_FROZEN_NOT_INDEPENDENT_VALIDATION":
        raise RuntimeError("NO_ORIGINAL_FROZEN_84_ROSTER")
    if roster["source_bat_GBIF_DOI"]!=EXPECTED["bat"]["doi"] or \
       roster["source_plant_GBIF_DOI"]!=EXPECTED["plant"]["doi"]:
        raise RuntimeError("ROSTER_DOI_CHANGED")
    if embargo.get("status")!="FULL_ORIGINAL_SITES_REFERENCE_EMBARGO_FROZEN" or \
       embargo.get("original_site_rows")!=200:
        raise RuntimeError("MISSING_ALL_SITES_SOURCE_EMBARGO")
    countries=roster["GBIF_29_country_universe"] if "GBIF_29_country_universe" in roster \
              else embargo["GBIF_29_country_universe"]
    site_banned=embargo["source_reference_embargo_by_holdout"]
    frozen=[(x["bat"],x["holdout_country"]) for x in roster["strict_84_candidate_folds"]]
    if len(frozen)!=84 or len(set(frozen))!=84:
        raise RuntimeError("FROZEN_PAIR_COUNT_OR_DUPLICATES")
    counts,totals=roster_matches(
        cells,links,bat_names,plant_names,countries,site_banned,frozen)
    rows=[one_fold(b,c,cells,links,counts,totals,plant_names,site_banned)
          for b,c in frozen]
    numeric=[
        "bat_cells_with_at_least_one_linked_plant_record",
        "bat_cells_with_at_least_three_linked_plant_species",
        "bat_cells_with_any_generic_plant_record",
        "bat_cells_with_linked_plant_from_distinct_GBIF_dataset"
    ]
    summary={
        "frozen_folds":len(rows),
        "folds_with_any_partner_same_cell_record":sum(r[numeric[0]]>0 for r in rows),
        "folds_with_three_partner_species_same_cell":sum(r[numeric[1]]>0 for r in rows),
        "folds_with_any_generic_same_cell_record":sum(r[numeric[2]]>0 for r in rows),
        "folds_with_any_partner_record_distinct_GBIF_dataset":sum(r[numeric[3]]>0 for r in rows),
        "folds_with_no_partner_same_cell_record":sum(r[numeric[0]]==0 for r in rows),
        "total_qualified_bat_recorded_cells_over_fold_rows":sum(r["known_precision_bat_recorded_cells"] for r in rows),
        "same_country_not_a_surveyed_absence":True
    }
    return {"schema_version":1,
            "status":"DOI_SOURCE_SAME_CELL_SUPPORT_DISCOVERY_NOT_MODEL",
            "created_utc":datetime.now(timezone.utc).isoformat(),
            "design":DESIGN,
            "original_NeoBat_commit":COMMIT,
            "GBIF_bat_DOI":EXPECTED["bat"]["doi"],
            "GBIF_plant_DOI":EXPECTED["plant"]["doi"],
            "GBIF_bat_archive_sha256":EXPECTED["bat"]["archive_sha"],
            "GBIF_plant_archive_sha256":EXPECTED["plant"]["archive_sha"],
            "cell_grid":"EPSG6933_25km_floor",
            "coordinate_uncertainty_m_le":12500,
            "same_cell_is_not_actual_feeding":True,
            "all_source_response_already_opened_discovery_only":True,
            "independent_test_response_unopened":False,
            "M3_minus_M1_heldout_auc":None,
            "M3_minus_N1_heldout_auc":None,
            "summary":summary,"frozen_fold_rows":rows}


def execute():
    roster=read(ROSTER)
    embargo=read(EMBARGO)
    complete=read(QC)
    archives=read(ARCHIVE_HEADER)
    if archives.get("status")!="BOTH_ARCHIVE_HEADERS_VERIFIED":
        raise RuntimeError("SOURCE_ARCHIVE_HEADER_NOT_VERIFIED")
    sources=verified_source(read(SUBMISSION),read(POLL))
    names=name_map(read(BAT_NAMES),read(PLANT_NAMES))
    tables={}
    for key in FILES:
        tables[key],_ = read_source(key)
    audit_bats={x for x in names["bat"].values()}
    audit_plants={x for x in names["plant"].values()}
    links=links_from_author_tables(
        tables["records"],tables["sites"],
        bats=audit_bats,plants=audit_plants)
    out={}
    with tempfile.TemporaryDirectory(prefix="neobat-source-same-cell-") as tmp:
        for group in GROUPS:
            expect=EXPECTED[group]
            source=sources[group]
            if source["doi"]!=expect["doi"] or \
               source["metadata_record_count"]!=expect["n_records"]:
                raise RuntimeError("SOURCE_DOI_DENOMINATOR_CHANGED_"+group)
            target=pathlib.Path(tmp)/(group+".zip")
            actual=safe_archive(source["url"],target)
            if actual["sha256"]!=expect["archive_sha"] or \
               actual["sha256"]!=archives["files"][group]["sha256"]:
                raise RuntimeError("SOURCE_ORIGINAL_ZIP_SHA_MISMATCH_"+group)
            data=strict_cell_records(target,group=group,
                    source=archives["files"][group],
                    accepted=names[group],expected_count=expect["n_records"])
            validate_against_full_qc(group,data,complete)
            out[group]=data
    result=aggregate(
        out,links,roster,embargo,
        sorted(audit_bats),sorted(audit_plants))
    result["both_original_GBIF_ZIPs_SHA_verified"]=True
    result["full_species_country_QC_exactly_replayed"]=True
    result["original_raw_coordinates_written_to_repo"]=False
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="build/neobat/same_cell_source_support.json")
    args=p.parse_args()
    dest=pathlib.Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=execute()
    except Exception as exc:
        result={"schema_version":1,
                "status":"SOURCE_SAME_CELL_SUPPORT_STOP",
                "error_type":type(exc).__name__,
                "error_code":str(exc)[:220],
                "design":DESIGN,
                "M3_minus_M1_heldout_auc":None,
                "M3_minus_N1_heldout_auc":None}
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("NEOBAT_SAME_CELL",result["status"],flush=True)
    if "summary" in result:
        print("SAME_CELL_SUMMARY",json.dumps(result["summary"],sort_keys=True),flush=True)
    return 0 if result["status"]=="DOI_SOURCE_SAME_CELL_SUPPORT_DISCOVERY_NOT_MODEL" else 3


if __name__=="__main__":
    raise SystemExit(main())
