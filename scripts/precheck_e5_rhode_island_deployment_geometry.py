#!/usr/bin/env python3
"""One-shot response-independent Rhode Island camera-deployment geometry audit.

The frozen Zenodo ZIP is transferred, but only the deployment CSV is opened.
No detection CSV stream, species, camera event time or biological response
values are inspected. Output contains only aggregate counts, never site IDs,
device names, coordinates, or individual dates.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
import hashlib
import io
import itertools
import json
import math
from pathlib import Path, PurePosixPath
import statistics
from urllib.request import Request, urlopen
import zipfile

EXPECTED_ID = "e5-rhode-island-metadata-only-deployment-geometry-v1"
EXPECTED_URL = "https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
EXPECTED_MD5 = "c66943e6c2a9aab0abce2a1eba8ce02e"
EXPECTED_BYTES = 12059878
EXPECTED_MEMBER = "RI_CameraSurvey_Deployments.csv"


def fetch_zip() -> bytes:
    req = Request(EXPECTED_URL, headers={"User-Agent": "esdm-E5-RI-metadata-only/1"})
    with urlopen(req, timeout=120) as response:
        data = response.read(EXPECTED_BYTES + 1)
    if len(data) != EXPECTED_BYTES:
        raise ValueError("frozen ZIP byte count mismatch")
    if hashlib.md5(data).hexdigest() != EXPECTED_MD5:
        raise ValueError("frozen Zenodo ZIP MD5 mismatch")
    return data


def parse_date(raw: str, formats: list[str]) -> date | None:
    s = str(raw).strip()
    if not s:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def float_coordinate(value: str, low: float, high: float) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and low <= x <= high else None


def calendar_months(start: date, end: date) -> set[int]:
    result = set()
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        result.add(month)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result


def stable_site_digest(site_id: str) -> str:
    return hashlib.sha256(site_id.encode("utf-8")).hexdigest()


def audit_deployment_csv(csv_bytes: bytes, contract: dict) -> dict:
    allowed = contract["source"]["allowed_member_fields"]
    if allowed != [
        "YearSeason", "Primary.Site.ID", "Trap.Station.Name", "Camera.Name",
        "Setup.Date", "Retrieval.Date", "Latitude", "Longitude"
    ]:
        raise ValueError("deployment-only column contract drift")
    r = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""))
    if r.fieldnames is None or r.fieldnames != allowed:
        raise ValueError("unexpected deployment table fields")
    datefmts = contract["grouping"]["accepted_date_formats"]
    records: list[dict] = []
    counts = Counter()
    site_coordinates: dict[str, list[tuple[float, float]]] = defaultdict(list)
    periods = Counter()

    for row in r:
        if set(row) != set(allowed) or any(v is None for v in row.values()):
            raise ValueError("malformed deployment record shape")
        counts["deployment_rows"] += 1
        season = row["YearSeason"].strip()
        site = row["Primary.Site.ID"].strip()
        station = row["Trap.Station.Name"].strip()
        camera = row["Camera.Name"].strip()
        if season:
            periods[season] += 1
        if not season or not site or not camera or not station:
            counts["missing_identifier_rows"] += 1
            continue
        lat = float_coordinate(row["Latitude"], -90, 90)
        lon = float_coordinate(row["Longitude"], -180, 180)
        if lat is None or lon is None:
            counts["invalid_coordinate_rows"] += 1
        else:
            site_coordinates[site].append((lat, lon))

        start = parse_date(row["Setup.Date"], datefmts)
        end = parse_date(row["Retrieval.Date"], datefmts)
        if start is None or end is None or end < start:
            counts["invalid_or_missing_effort_date_rows"] += 1
            continue
        if (end - start).days > 3650:
            counts["unreasonably_long_deployment_rows"] += 1
            continue
        counts["valid_effort_rows"] += 1
        records.append({
            "season": season, "site": site, "station": station,
            "camera": camera, "start": start, "end": end,
        })

    if counts["deployment_rows"] == 0:
        raise ValueError("empty deployment table")

    site_meta = {}
    spatial_conflicts = 0
    max_span = float(contract["grouping"]["location_consistency"].split("<=")[1].split()[0])
    for site, locs in site_coordinates.items():
        lats = [x[0] for x in locs]
        lons = [x[1] for x in locs]
        if max(lats)-min(lats)>max_span or max(lons)-min(lons)>max_span:
            spatial_conflicts += 1
            continue
        site_meta[site] = (statistics.median(lats), statistics.median(lons))

    ordered_sites = sorted(
        site_meta, key=lambda site:(site_meta[site][1],stable_site_digest(site))
    )
    n_west = len(ordered_sites)//2
    geographic_block = {
        site: ("WEST_OPERATIONAL" if i<n_west else "EAST_OPERATIONAL")
        for i,site in enumerate(ordered_sites)
    }
    groups: dict[tuple[str,str],list[dict]]=defaultdict(list)
    for rec in records:
        groups[(rec["site"],rec["season"])].append(rec)

    group_results = {}
    pair_count_by_period=Counter()
    pair_overlap_by_period=Counter()
    paired_sites_by_block=defaultdict(set)
    operational_overlaps_by_block=Counter()
    for (site,season),rr in groups.items():
        cameras = {x["camera"] for x in rr}
        stations = {x["station"] for x in rr}
        two_members = len(cameras)>=2 and len(stations)>=2
        overlap = any(
            a["camera"]!=b["camera"] and a["station"]!=b["station"]
            and max(a["start"],b["start"]) <= min(a["end"],b["end"])
            for a,b in itertools.combinations(rr,2)
        )
        if two_members:
            pair_count_by_period[season] += 1
        if overlap:
            pair_overlap_by_period[season] += 1
        group_results[(site,season)] = {
            "two_members": two_members,
            "positive_overlap": overlap,
        }
        block = geographic_block.get(site)
        if block and overlap:
            paired_sites_by_block[block].add(site)
            operational_overlaps_by_block[block] += 1

    exposures = {"WEST_OPERATIONAL":set(), "EAST_OPERATIONAL":set()}
    physical_sites = {"WEST_OPERATIONAL":set(), "EAST_OPERATIONAL":set()}
    valid_deployments_by_block=Counter()
    for rec in records:
        block = geographic_block.get(rec["site"])
        if not block:
            continue
        valid_deployments_by_block[block] += 1
        physical_sites[block].add(rec["site"])
        exposures[block] |= calendar_months(rec["start"], rec["end"])

    block_results = {}
    for block in ("WEST_OPERATIONAL","EAST_OPERATIONAL"):
        block_results[block] = {
            "valid_effort_rows":valid_deployments_by_block[block],
            "independent_physical_sites_with_valid_effort":len(physical_sites[block]),
            "physical_sites_with_matched_camera_overlap":len(paired_sites_by_block[block]),
            "site_periods_with_matched_camera_overlap":operational_overlaps_by_block[block],
            "distinct_calendar_months_of_deployment_exposure":len(exposures[block]),
            "calendar_month_numbers":sorted(exposures[block]),
        }

    west=block_results["WEST_OPERATIONAL"]
    east=block_results["EAST_OPERATIONAL"]
    physical = (
        west["independent_physical_sites_with_valid_effort"]>=20
        and east["independent_physical_sites_with_valid_effort"]>=20
    )
    months = all(
        z["distinct_calendar_months_of_deployment_exposure"]>=6
        for z in (west,east)
    )
    paired = all(
        z["site_periods_with_matched_camera_overlap"]>0
        for z in (west,east)
    )
    status = (
        "DEPLOYMENT_GEOMETRY_SUPPORTS_NEXT_G4_STRUCTURAL_REVIEW"
        if physical and months and paired and spatial_conflicts==0
        else "DEPLOYMENT_GEOMETRY_INCOMPLETE_OR_QC_HOLD"
    )
    period_results=[]
    for season in sorted(periods):
        paired_rows=pair_count_by_period[season]
        overlaps=pair_overlap_by_period[season]
        period_results.append({
            "survey_period":season,
            "deployment_metadata_rows":periods[season],
            "site_periods_with_two_named_camera_members":paired_rows,
            "site_periods_with_matched_camera_overlap":overlaps,
        })

    return {
        "schema_version":1,
        "candidate_id":"rhode_island_paired_cameras_2018_2023",
        "route_id":contract["contract_id"],
        "status":status,
        "deployment_summary":{
            "total_rows":counts["deployment_rows"],
            "missing_identifier_rows":counts["missing_identifier_rows"],
            "invalid_coordinate_rows":counts["invalid_coordinate_rows"],
            "invalid_or_missing_effort_date_rows":counts["invalid_or_missing_effort_date_rows"],
            "unreasonably_long_deployment_rows":counts["unreasonably_long_deployment_rows"],
            "valid_effort_rows":counts["valid_effort_rows"],
            "spatially_inconsistent_site_ids":spatial_conflicts,
            "physical_site_ids_with_consistent_coordinates":len(site_meta),
            "valid_site_period_groups":len(groups),
        },
        "survey_periods":period_results,
        "geographic_operational_blocks":block_results,
        "response_boundary":{
            "full_ZIP_archive_containing_biological_records_transferred":True,
            "deployment_metadata_rows_processed":counts["deployment_rows"],
            "detection_CSV_stream_opened":False,
            "taxon_values_read":False,
            "event_datetime_values_read":False,
            "biological_response_rows_processed":0,
            "raw_site_or_camera_ID_values_uploaded":False,
            "raw_lat_lon_or_individual_dates_uploaded":False,
            "fitted_model_count":0,
        },
        "decision":{
            "operational_split_physical_replication_minima_met":physical,
            "operational_split_six_calendar_months_met":months,
            "within_site_paired_member_operational_overlap_in_both_blocks":paired,
            "original_public_west_east_sections_verified":False,
            "G2_full_pass_authorized":False,
            "G3_final_pass_authorized":False,
            "G4_effective_detection_pass_authorized":False,
            "G5_aggregate_physical_capacity_provisional":physical,
            "G6_calendar_month_coverage_provisional":months,
            "candidate_qualified":False,
            "focal_response_opening_authorized":False,
            "model_fitting_authorized":False,
        },
    }


def run(contract: dict) -> dict:
    if contract.get("contract_id") != EXPECTED_ID:
        raise ValueError("contract ID drift")
    if contract.get("status") != "FROZEN_METADATA_ONLY_GEOMETRY_NOT_AUTHORIZED":
        raise ValueError("contract not frozen")
    scope=contract["scope"]
    for forbidden in (
        "detection_CSV_stream_open_authorized",
        "taxon_values_open_authorized",
        "event_datetime_values_open_authorized",
        "biological_outcomes_open_authorized",
        "modeling_or_selection_by_biological_values_authorized",
        "raw_deployment_site_ids_in_output_authorized",
        "raw_coordinates_or_exact_dates_in_output_authorized",
    ):
        if scope.get(forbidden) is not False:
            raise ValueError("response/metadata privacy boundary drift")
    src=contract["source"]
    if src["archive_download_url"] != EXPECTED_URL:
        raise ValueError("source URL drift")
    if src["archive_bytes"] != EXPECTED_BYTES or src["archive_md5"] != EXPECTED_MD5:
        raise ValueError("source ZIP identity drift")
    if src["allowed_member"] != EXPECTED_MEMBER:
        raise ValueError("source deployment member drift")
    blob=fetch_zip()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        candidates=[
            x for x in archive.infolist()
            if not x.is_dir() and PurePosixPath(x.filename).name==EXPECTED_MEMBER
        ]
        if len(candidates)!=1:
            raise ValueError("expected exactly one deployment metadata member")
        # The detection member is NEVER opened.
        with archive.open(candidates[0]) as stream:
            rows=stream.read(2_000_000)
        if len(rows)!=273870:
            raise ValueError("unexpected deployment member uncompressed size")
    value=audit_deployment_csv(rows,contract)
    value["source_receipt"]={
        "zenodo_record_id":14508932,
        "zip_bytes":len(blob),
        "zip_md5":EXPECTED_MD5,
        "deployment_member_uncompressed_bytes":len(rows),
        "detection_member_opened":False,
    }
    return value


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--contract",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    value=run(contract)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
