"""Stream and aggregate complete, DOI-backed NeoBat GBIF SIMPLE_CSV ZIP sources.

This opens full occurrence data for *discovery source QC only*. Never exports
records, exact coordinates, event IDs, or biological model predictions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import pathlib
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import zipfile

from scripts.neobat_gbif_archive_header_preflight import verified_source, safe_archive
from scripts.neobat_spatial_cell_pilot import spatial_grid, label_precision

GROUPS=("bat","plant")
EXPECTED_KEY_COUNTS={"bat":26,"plant":255}
ALLOWED_YEAR=range(2000,2026)
REQUIRED_FIELDS={"gbifID","speciesKey","taxonKey","datasetKey","countryCode",
                 "decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters",
                 "year","basisOfRecord","occurrenceID"}

def name_map(batmeta, plantmeta):
    rows={
      "bat":[r for r in batmeta["records"] if r.get("status") in
             ("GBIF_COUNTS_ONLY","GBIF_COUNTS_AUDITED_ALIAS")],
      "plant":[r for r in plantmeta["plants"] if r.get("status")=="GBIF_PLANT_COUNTS_ONLY"]
    }
    mapping={}
    for group, rr in rows.items():
        if len(rr)!=EXPECTED_KEY_COUNTS[group]:
            raise RuntimeError("SOURCE_NAME_COUNT_MISMATCH_"+group)
        obj={}
        for r in rr:
            key=str(r["match"].get("acceptedUsageKey") or r["match"]["usageKey"])
            name=r["bat"] if group=="bat" else r["plant"]
            if key in obj:raise RuntimeError("SOURCE_TAXON_KEY_COLLISION_"+group)
            obj[key]=name
        mapping[group]=obj
    return mapping

def source_header_matches(actual, source):
    if actual!=source:
        raise RuntimeError("SOURCE_TSV_HEADER_MISMATCH")
    if not REQUIRED_FIELDS.issubset(set(actual)):
        raise RuntimeError("SOURCE_REQUIRED_FIELDS_MISSING")
    return True

def quality_counts_for_archive(path, *, group, source, accepted, expected_count):
    """Hold cell ids and source-event identifiers only in process memory."""
    import zipfile
    allowed_key=set(accepted)
    cells=defaultdict(set)
    cells50=defaultdict(set)
    strict=defaultdict(set)
    strict50=defaultdict(set)
    datasets=defaultdict(set)
    by_country_basis=defaultdict(Counter)
    species_counts=Counter()
    species_uncertainty=defaultdict(Counter)
    overall=Counter()
    gbif_ids=set()
    source_events=set()
    member_name=source["zip_entry_name"]
    with zipfile.ZipFile(path) as archive:
        if member_name not in archive.namelist():
            raise RuntimeError("SOURCE_ZIP_MEMBER_MISSING")
        with archive.open(member_name) as stream:
            reader=csv.DictReader(io.TextIOWrapper(stream,encoding="utf-8-sig",newline=""),
                                  delimiter="\t",quoting=csv.QUOTE_MINIMAL)
            source_header_matches(reader.fieldnames,source["header_columns"])
            for r in reader:
                overall["rows"]+=1
                if not r or any(v is None for v in r.values()):
                    overall["tsv_malformed"]+=1
                    continue
                key=str(r.get("speciesKey") or "")
                taxon=str(r.get("taxonKey") or "")
                if key not in allowed_key:
                    overall["unmatched_species_key"]+=1
                    if taxon in allowed_key:
                        overall["taxon_key_contradiction"]+=1
                    continue
                name=accepted[key]
                species_counts[name]+=1
                gid=str(r.get("gbifID") or "").strip()
                if not gid:
                    overall["gbif_id_missing"]+=1
                elif gid in gbif_ids:
                    overall["duplicate_gbif_id"]+=1
                    continue
                else:
                    gbif_ids.add(gid)
                ds=str(r.get("datasetKey") or "").strip()
                eventid=str(r.get("occurrenceID") or "").strip()
                if ds and eventid:
                    identity=(ds,eventid)
                    if identity in source_events:
                        overall["duplicate_dataset_occurrenceid"]+=1
                    else:
                        source_events.add(identity)
                else:
                    overall["source_event_id_missing"]+=1
                cc=str(r.get("countryCode") or "").strip()
                year=str(r.get("year") or "").strip()
                try:
                    yr=int(year)
                except (TypeError,ValueError):
                    yr=None
                if yr not in ALLOWED_YEAR:
                    overall["year_outside_or_missing"]+=1
                    continue
                if len(cc)!=2 or not cc.isupper():
                    overall["country_malformed"]+=1
                    continue
                try:
                    lat=float(r.get("decimalLatitude"))
                    lon=float(r.get("decimalLongitude"))
                except (TypeError,ValueError):
                    overall["coordinate_unparseable"]+=1
                    continue
                xy=spatial_grid(lon,lat)
                if xy is None:
                    overall["coordinate_invalid"]+=1
                    continue
                overall["valid_source_rows"]+=1
                cells[(name,cc)].add(xy[0])
                cells50[(name,cc)].add(xy[1])
                precision=label_precision(r.get("coordinateUncertaintyInMeters"))
                species_uncertainty[name][precision]+=1
                overall["precision_"+precision]+=1
                if precision=="known_le_12_5km":
                    strict[(name,cc)].add(xy[0])
                    strict50[(name,cc)].add(xy[1])
                if ds: datasets[(name,cc)].add(ds)
                by_country_basis[(name,cc)][str(r.get("basisOfRecord") or "UNKNOWN")]+=1
    if overall["rows"]!=expected_count:
        raise RuntimeError("ARCHIVE_GBIF_RECORD_DENOMINATOR_MISMATCH")
    out=[]
    for key in sorted(set(cells)|set(strict),key=lambda z:(z[0],z[1])):
        name,cc=key
        out.append({
            "taxon":name,"country":cc,
            "recorded_25km_cells":len(cells[key]),
            "recorded_50km_cells":len(cells50[key]),
            "precision_le12500m_25km_cells":len(strict[key]),
            "precision_le12500m_50km_cells":len(strict50[key]),
            "source_datasets":len(datasets[key]),
            "basis_counts":dict(sorted(by_country_basis[key].items()))
        })
    species_summary=[]
    for name in sorted(accepted.values()):
        country_cells=[z for z in out if z["taxon"]==name]
        species_summary.append({
            "taxon":name,"indexed_records_matching_species":species_counts[name],
            "countries_with_records":len(country_cells),
            "country_cells":sum(z["recorded_25km_cells"] for z in country_cells),
            "known_precision_country_cells":sum(z["precision_le12500m_25km_cells"] for z in country_cells),
            "countries_with_ge5_recorded_cells":sum(z["recorded_25km_cells"]>=5 for z in country_cells),
            "countries_with_ge5_known_precision_cells":sum(z["precision_le12500m_25km_cells"]>=5 for z in country_cells),
            "candidate_country_5cell_vs_20_outside":sum(
                z["recorded_25km_cells"]>=5 and
                sum(w["recorded_25km_cells"] for w in country_cells if w["country"]!=z["country"])>=20
                for z in country_cells),
            "uncertainty_records":dict(species_uncertainty[name])
        })
    return {
        "status":"FULL_GBIF_RECORD_SOURCE_QC_ONLY",
        "group":group,
        "GBIF_source_record_count":expected_count,
        "full_archive_rows_checked":overall["rows"],
        "valid_source_rows":overall["valid_source_rows"],
        "quality_breakdown":dict(sorted(overall.items())),
        "unique_gbif_ids_seen":len(gbif_ids),
        "duplicate_dataset_occurrence_id_count":overall["duplicate_dataset_occurrenceid"],
        "distinct_species_with_valid_cells":sum(x["countries_with_records"]>0 for x in species_summary),
        "species_summary":species_summary,
        "species_country_summary":out,
        "independent_survey_absences":False,
        "spatial_holdout_confirmed":False,
        "M3_minus_M1":None
    }

def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--submission",default="docs/replication/neobat/gbif_download_submission.json")
    pa.add_argument("--doi-poll",default="docs/replication/neobat/gbif_download_doi_poll.json")
    pa.add_argument("--archive-receipt",default="docs/replication/neobat/gbif_archive_header_preflight.json")
    pa.add_argument("--bat-name-meta",default="docs/replication/neobat/gbif_search_preflight.json")
    pa.add_argument("--plant-name-meta",default="docs/replication/neobat/plant_search_preflight.json")
    pa.add_argument("--out",default="build/neobat/gbif_full_source_qc.json")
    args=pa.parse_args()
    dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    result={"schema_version":1,"created_utc":datetime.now(timezone.utc).isoformat(),
            "status":"FULL_SOURCE_QC_NOT_STARTED","groups":{},
            "never_committed_occurrence_rows":True,"ecological_result":None}
    try:
        def read(path): return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        submission=read(args.submission)
        poll=read(args.doi_poll)
        header=read(args.archive_receipt)
        names=name_map(read(args.bat_name_meta),read(args.plant_name_meta))
        sources=verified_source(submission,poll)
        if header.get("status")!="BOTH_ARCHIVE_HEADERS_VERIFIED":
            raise RuntimeError("SOURCE_ARCHIVE_RECEIPT_NOT_VERIFIED")
        with tempfile.TemporaryDirectory(prefix="neobat-raw-only-") as tmp:
            for group in GROUPS:
                target=pathlib.Path(tmp)/(group+".zip")
                source=sources[group]
                recorded=header["files"][group]
                if recorded["download_key"]!=source["download_key"] or recorded["doi"]!=source["doi"]:
                    raise RuntimeError("SOURCE_KEY_DOI_CONFLICT_"+group)
                download=safe_archive(source["url"],target)
                if download["sha256"]!=recorded["sha256"]:
                    raise RuntimeError("SOURCE_HASH_MISMATCH_"+group)
                qc=quality_counts_for_archive(target,group=group,source=recorded,
                                              accepted=names[group],
                                              expected_count=source["metadata_record_count"])
                qc["source_archive_sha256"]=download["sha256"]
                qc["DOI"]=source["doi"]
                result["groups"][group]=qc
                result["status"]="PARTIAL_FULL_SOURCE_QC"
                dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
                print("FULL_SOURCE_QC_GROUP",group,qc["full_archive_rows_checked"],
                      qc["valid_source_rows"],flush=True)
        result["status"]="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED"
    except Exception as exc:
        result["status"]="FULL_SOURCE_QC_STOP"
        result["error_type"]=type(exc).__name__
        result["error_code"]=str(exc)[:200]
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("FULL_SOURCE_QC",result["status"],flush=True)
    return 0 if result["status"]=="BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED" else 3

if __name__=="__main__":
    raise SystemExit(main())
