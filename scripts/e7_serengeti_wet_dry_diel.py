#!/usr/bin/env python3
"""Independent, outcome-labelled E7 wet/dry mammal relative-diel community audit.

Source: LILA Snapshot Serengeti per-season COCO Camera Traps metadata only.
Never downloads images; deduplicates all image annotations to sequences.
S01..S05 define the taxon roster *before* S06..S11 responses are inspected.
Output contains aggregate category, period and support summaries only.
"""
from __future__ import annotations

import argparse
import gc
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import re
import zipfile


DISCOVERY = tuple(range(1, 6))
VALIDATION = tuple(range(6, 12))
EXPECTED_SOURCE_SHA256 = {
    "S01": "5b0b004c58e05f97cc23d0b572bfd3e63b6d52c9297cb031ef81eb700f762c29",
    "S02": "1c33f782ecc5ab2dc005683e6e0ca328ebf37993316aae311b26a9b44caffb56",
    "S03": "b2732aa283b1d1dde03b210f0951dd0a587ec8c659818aecb5b986e36cd78962",
    "S04": "913fa6a8bb90a004d149446c23e0fc4d707121d6527d3e4a696e619f3fc71835",
    "S05": "9da4b5ce311728e3e4d494921c04ba0e3470b260ce1936f932e5a6b62ff9bb75",
    "S06": "0d1e59a76ee46b5fa8bcbe8943ccb239b3fcac588549e2b7c5cf1315f548ccb8",
    "S07": "9b23a59dc9e56e187f40f6b5338d1f9e0ed2ed6aaba519ab8d9d5f92f78b35a2",
    "S08": "2868d5d33358160ca2c0859c4ea4de1cf3c981f8930ec594cf33cad974814f2f",
    "S09": "9c0754681c4f926a45e3225e7a33b29ebe1688c41323feb3d6084fc4ed7477fd",
    "S10": "8e0021a537e64d85275ae6074910c4664c2f4e226c6be4c47a885b02ed1b049b",
    "S11": "57b4618eee202f0ab1a4f64dfed78f17fa6d9631c0a815d9fa4252079614f3d7"
}

TOP_N = 12
MIN_SITES = 5
MIN_SITE_YEARS = 10
MIN_ORIGINAL_COLLECTION_SEASONS = 3

# Fixed independently of any E7 empirical response. Distinct subspecies/sex
# labels are only pooled for lion; unrecognized or nonmammalian labels are
# excluded rather than selected by apparent ecological effect.
_RAW_MAMMALS = (
    "aardvark aardwolf baboon batEaredFox buffalo bushbuck caracal cheetah "
    "civet dikDik duiker eland elephant gazelleGrants gazelleThomsons genet "
    "giraffe hare hartebeest hippopotamus honeyBadger hyenaSpotted "
    "hyenaStriped impala jackal leopard lionFemale lionMale lioncub "
    "mongoose porcupine reedbuck rhinoceros rodents serval topi "
    "vervetMonkey warthog waterbuck wildcat wildebeest zebra zorilla"
)
MAMMALS = {
    re.sub(r"[^a-z]", "", name.lower()): name
    for name in _RAW_MAMMALS.split()
}
for synonym in ("lionmale", "lionfemale", "lioncub"):
    MAMMALS[synonym] = "lion"


def normal_name(raw: str) -> str | None:
    return MAMMALS.get(re.sub(r"[^a-z]", "", str(raw).lower()))


def climatological_phase(month: int) -> str | None:
    if month in (11, 12, 1, 2, 3, 4):
        return "wet"
    if month in (6, 7, 8, 9):
        return "dry"
    return None


def clock_period(hour: int) -> str | None:
    if hour >= 21 or hour <= 3:
        return "night"
    if 10 <= hour <= 15:
        return "midday"
    return None


def water_year(dt: datetime) -> int:
    return dt.year if dt.month >= 11 else dt.year - 1


def parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts).strip())


def _member(z: zipfile.ZipFile) -> str:
    matches = [name for name in z.namelist() if name.lower().endswith(".json")
               and not name.endswith("/")]
    if len(matches) != 1:
        raise ValueError(f"metadata ZIP must contain exactly one JSON: {matches}")
    return matches[0]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_season(path: Path, season: int, counts: Counter, occupancy: dict,
                 folder_support: dict) -> dict:
    """Streaming COCO JSON parsing, one season resident in RAM at a time."""
    qc = Counter()
    if not zipfile.is_zipfile(path):
        raise ValueError("not a downloaded metadata ZIP")
    with zipfile.ZipFile(path) as archive:
        member = _member(archive)
        # LILA COCO JSON contains nonstandard bare NaN values in optional
        # consensus count/behavior fields; the default streaming JSON parser
        # refuses them. The standard-library decoder accepts these tokens.
        # They are normalized to None and NEVER used in the diel analysis.
        with archive.open(member) as handle:
            doc = json.load(handle, parse_constant=lambda _: None)
        with archive.open(member) as f:
            category_ids = {}
            for c in doc["categories"]:
                category_ids[str(c["id"])] = normal_name(c.get("name", ""))
        if len(category_ids) < 10:
            raise ValueError("unexpectedly sparse COCO categories")
        image_to_seq = {}
        seq_meta = {}
        conflicts = set()
        with archive.open(member) as f:
            for img in doc["images"]:
                qc["images"] += 1
                imageid, seq = str(img.get("id", "")), str(img.get("seq_id", ""))
                loc, date_text = str(img.get("location","")), str(img.get("datetime",""))
                if not imageid or not seq or not loc or not date_text:
                    qc["incomplete_images"] += 1
                    continue
                try:
                    stamp = parse_timestamp(date_text)
                except (ValueError, TypeError):
                    qc["invalid_datetime"] += 1
                    continue
                if imageid in image_to_seq and image_to_seq[imageid] != seq:
                    raise ValueError("one image maps to conflicting sequence IDs")
                image_to_seq[imageid] = seq
                old = seq_meta.get(seq)
                if old is None:
                    seq_meta[seq] = (loc, stamp)
                elif old[0] != loc:
                    conflicts.add(seq)
                elif stamp < old[1]:
                    seq_meta[seq] = (loc, stamp)
        qc["distinct_sequences_with_image_metadata"] = len(seq_meta)
        doc.pop("images", None)
        gc.collect()
        qc["conflicting_sequence_locations"] = len(conflicts)
        seen = set()
        with archive.open(member) as f:
            for item in doc["annotations"]:
                qc["annotations"] += 1
                name = category_ids.get(str(item.get("category_id", "")))
                if name is None:
                    qc["nonmammalian_or_unidentified_annotation"] += 1
                    continue
                seq = image_to_seq.get(str(item.get("image_id", "")))
                if not seq or seq in conflicts or seq not in seq_meta:
                    qc["unjoined_or_ambiguous_annotation"] += 1
                    continue
                key = (seq, name)
                if key in seen:
                    qc["duplicate_image_annotation_in_sequence"] += 1
                    continue
                seen.add(key)
                loc, stamp = seq_meta[seq]
                phase = climatological_phase(stamp.month)
                if phase is None:
                    qc["transition_month_excluded"] += 1
                    continue
                hydro = water_year(stamp)
                siteyear = (loc, hydro)
                occupancy[name].add(siteyear)
                qc["valid_species_sequences_all_hours"] += 1
                clock = clock_period(stamp.hour)
                if clock is None:
                    qc["twilight_or_offwindow_sequence"] += 1
                    continue
                counts[(loc, hydro, phase, name, clock)] += 1
                folder_support[(loc, hydro, phase)].add(season)
                qc["valid_focal_hour_sequences"] += 1
    del doc
    gc.collect()
    qc["collection_season"] = season
    return dict(qc)


def choose_discovery_panel(counts: Counter, occupancy: dict) -> list[str]:
    # Ties after camera-hydrological-year occupancy use positive sequence
    # frequency; no diel, dry/wet effect or validation outcomes may enter.
    totals = Counter()
    for (_, _, _, name, _), n in counts.items():
        totals[name] += n
    ordered = sorted(
        occupancy,
        key=lambda n: (-len(occupancy[n]), -totals[n], n),
    )
    return ordered[:TOP_N]


def matched_siteyears(counts: Counter, folders: dict, a: str, b: str) -> list[dict]:
    candidates = {
        (loc, water) for loc, water, phase, name, clock in counts.keys()
        if name in (a, b)
    }
    matched = []
    for loc, hydro in sorted(candidates):
        by_phase = {}
        good = True
        for phase in ("wet", "dry"):
            x, y = counts[(loc, hydro, phase, a, "night")], counts[(loc, hydro, phase, a, "midday")]
            u, v = counts[(loc, hydro, phase, b, "night")], counts[(loc, hydro, phase, b, "midday")]
            if min(x+y, u+v, x+u, y+v) <= 0:
                good = False
                break
            by_phase[phase] = (x, y, u, v)
        if good:
            seasons = set(folders.get((loc, hydro, "wet"), ()))
            seasons.update(folders.get((loc, hydro, "dry"), ()))
            matched.append({"site":loc, "year":hydro,
                            "tables":by_phase, "source_seasons":seasons})
    return matched


def _mh(rows: list[dict], phase: str):
    numerator = denominator = 0.0
    for r in rows:
        a,b,c,d = r["tables"][phase]
        n=a+b+c+d
        numerator += a*d/n
        denominator += b*c/n
    if numerator <= 0 or denominator <= 0:
        return None
    return numerator / denominator


def pair_estimate(rows: list[dict], *, threshold: bool=True) -> dict:
    sites = {r["site"] for r in rows}
    seasons = set().union(*(r["source_seasons"] for r in rows)) if rows else set()
    meta = {"matched_site_years":len(rows),"matched_distinct_sites":len(sites),
            "supporting_original_seasons":len(seasons)}
    if threshold and (len(sites)<MIN_SITES or len(rows)<MIN_SITE_YEARS
                      or len(seasons)<MIN_ORIGINAL_COLLECTION_SEASONS):
        return {**meta, "status":"INSUFFICIENT_MATCHED_CAMERA_YEARS",
                "wet_odds":None,"dry_odds":None,"relative_shift":None}
    wet, dry = _mh(rows,"wet"),_mh(rows,"dry")
    if wet is None or dry is None:
        return {**meta, "status":"ZERO_OR_INFINITE_MH_PRODUCT",
                "wet_odds":None,"dry_odds":None,"relative_shift":None}
    return {**meta,"status":"DESCRIPTIVE_ESTIMABLE",
            "wet_odds":wet,"dry_odds":dry,"relative_shift":dry/wet}


def per_pair(counts: Counter, folders: dict, a: str,b: str) -> dict:
    rows = matched_siteyears(counts,folders,a,b)
    result=pair_estimate(rows)
    loo=[]
    if result["status"]=="DESCRIPTIVE_ESTIMABLE" and result["matched_distinct_sites"]>MIN_SITES:
        for site in sorted({r["site"] for r in rows}):
            subset=[r for r in rows if r["site"]!=site]
            v=pair_estimate(subset)
            if v["status"]=="DESCRIPTIVE_ESTIMABLE":
                loo.append(v)
    full=len(loo)==len({r["site"] for r in rows}) and bool(loo)
    wetlo = min((r["wet_odds"] for r in loo),default=None)
    wethi = max((r["wet_odds"] for r in loo),default=None)
    drylo = min((r["dry_odds"] for r in loo),default=None)
    dryhi = max((r["dry_odds"] for r in loo),default=None)
    reversal=bool(result["status"]=="DESCRIPTIVE_ESTIMABLE"
        and ((result["wet_odds"]<1<result["dry_odds"])
        or (result["dry_odds"]<1<result["wet_odds"])))
    stable=bool(full and reversal and
        ((wethi<1<drylo) or (dryhi<1<wetlo)))
    return {
        "species_1":a,"species_2":b,**result,
        "rank_reversal_in_recorded_diel_odds":reversal,
        "leave_one_site_out_all_computable":full,
        "leave_one_site_out_wet_range":[wetlo,wethi],
        "leave_one_site_out_dry_range":[drylo,dryhi],
        "rank_reversal_stable_under_site_deletion":stable,
    }


def all_pair_results(counts: Counter, folders: dict, roster: list[str]) -> dict:
    pairs=[per_pair(counts,folders,a,b) for a,b in combinations(sorted(roster),2)]
    return {
        "fixed_taxa":list(sorted(roster)),
        "possible_pairs":len(pairs),
        "comparable_pairs":sum(p["status"]=="DESCRIPTIVE_ESTIMABLE" for p in pairs),
        "relative_diel_rank_reversals":sum(p["rank_reversal_in_recorded_diel_odds"] for p in pairs),
        "single_site_stable_reversals":sum(p["rank_reversal_stable_under_site_deletion"] for p in pairs),
        "all_pairs":pairs,
    }


def run(input_dir: Path) -> dict:
    counts_train, counts_valid = Counter(),Counter()
    occupancy=defaultdict(set)
    source_train=defaultdict(set)
    source_valid=defaultdict(set)
    digests={}
    qc={}
    for season in DISCOVERY:
        path=input_dir/f"SnapshotSerengetiS{season:02d}.json.zip"
        digest=sha256(path)
        if digest != EXPECTED_SOURCE_SHA256[f"S{season:02d}"]:
            raise ValueError("LILA metadata ZIP bytes differ from pinned first download")
        digests[f"S{season:02d}"]=digest
        qc[f"S{season:02d}"]=parse_season(path,season,counts_train,occupancy,source_train)
    roster=choose_discovery_panel(counts_train,occupancy)
    if len(roster)<2:
        raise ValueError("INSUFFICIENT_ROSTER")
    print("FROZEN_E7_DISCOVERY_PANEL_BEFORE_HOLDOUT="+json.dumps(roster),flush=True)
    train_results=all_pair_results(counts_train,source_train,roster)
    # E7 validation files are opened only after roster has been fixed.
    for season in VALIDATION:
        path=input_dir/f"SnapshotSerengetiS{season:02d}.json.zip"
        digest=sha256(path)
        if digest != EXPECTED_SOURCE_SHA256[f"S{season:02d}"]:
            raise ValueError("LILA metadata ZIP bytes differ from pinned first download")
        digests[f"S{season:02d}"]=digest
        qc[f"S{season:02d}"]=parse_season(path,season,counts_valid,
                                           defaultdict(set),source_valid)
    val_results=all_pair_results(counts_valid,source_valid,roster)
    by_pair={
        (r["species_1"],r["species_2"]):r
        for r in train_results["all_pairs"]
    }
    transfers=[]
    for r in val_results["all_pairs"]:
        old=by_pair[r["species_1"],r["species_2"]]
        good=old["status"]==r["status"]=="DESCRIPTIVE_ESTIMABLE"
        concordant=bool(good and
            (math.log(old["relative_shift"])*math.log(r["relative_shift"])>0))
        transfers.append({
            "species_1":r["species_1"],"species_2":r["species_2"],
            "both_periods_comparable":good,
            "direction_concordant":concordant,
            "train_seasonal_log_ratio":math.log(old["relative_shift"]) if good else None,
            "validation_seasonal_log_ratio":math.log(r["relative_shift"]) if good else None,
            "site_deletion_stable_both":bool(
                concordant and old["rank_reversal_stable_under_site_deletion"]
                and r["rank_reversal_stable_under_site_deletion"]),
        })
    return {
        "status":"E7_SERENGETI_INDEPENDENT_SEASONAL_ASSEMBLY_EXPLORATORY_RESULT",
        "date":"2026-10-19",
        "frozen_design":"docs/replication/E7_SERENGETI_WET_DRY_COMMUNITY_FROZEN_DESIGN.md",
        "source_archive_sha256":digests,
        "source_season_qc":qc,
        "roster_selected_before_validation":roster,
        "discovery":train_results,
        "validation":val_results,
        "season_index_transfer":{
            "both_comparable_pairs":sum(r["both_periods_comparable"] for r in transfers),
            "direction_concordant_pairs":sum(r["direction_concordant"] for r in transfers),
            "stable_reversal_in_both_and_direction_concordant":sum(r["site_deletion_stable_both"] for r in transfers),
            "all_66_pairs":transfers,
        },
        "claim_limits":{
            "new_biological_dataset_independent_of_E4_MICA":True,
            "independent_response_validation_seasons":True,
            "camera_locations_may_repeat_between_periods":True,
            "dry_wet_measured_rainfall_per_site":False,
            "recorded_event_time_not_independently_calibrated_activity":True,
            "no_image_files_downloaded":True,
            "human_class_removed_from_analysis":True,
            "no_raw_site_or_sequence_identifiers_output":True,
            "E4_frozen_fit_changed":False,
            "E5_original_G4_passed":False,
            "E5_standard_qualified_datasets":0,
            "new_event_level_p_values_or_confidence_intervals":False,
        }
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=run(args.input_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "panel":result["roster_selected_before_validation"],
        "discovery_comparable":result["discovery"]["comparable_pairs"],
        "validation_comparable":result["validation"]["comparable_pairs"],
        "both_comparable":result["season_index_transfer"]["both_comparable_pairs"],
        "direction_concordant":result["season_index_transfer"]["direction_concordant_pairs"],
        "stable_reversals_both":result["season_index_transfer"]["stable_reversal_in_both_and_direction_concordant"]
    },sort_keys=True))


if __name__=="__main__":
    main()
