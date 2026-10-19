#!/usr/bin/env python3
"""E6: frozen SNAPSHOT USA mammal-community temporal-assembly macroanalysis.

A *separate* observation-based ecological study, NOT an E4 refit, E5 G4 pass,
causal estimate of urban development, or independently calibrated activity.
Source files are official pinned Dryad bytes; 2024 never selects taxa.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import re

DATA = {
    "history": {
        "deployment_sha256": "9e837bba556de86af5934abcb5d8a487206df2b340a8b28fa8cc135c7bb7ec56",
        "sequence_sha256": "8a442b130f11272c354de10ff97f69c65ae738a6514459f1431e963708011ded",
        "doi": "10.5061/dryad.k0p2ngfhn",
    },
    "holdout_2024": {
        "deployment_sha256": "b742e8789fa18c83713f2dec76e342857c122c012ee464db5563f3b06d29970d",
        "sequence_sha256": "252724a52bf656b2d1dda7d07018ccdc5ad571c0011eee33a05eccf12e005d2a",
        "doi": "10.5061/dryad.bnzs7h4qf",
    },
}
LOW = {"wild", "rural"}
HIGH = {"suburban", "urban"}
EXCLUDED_TAXA = {
    "Homo sapiens", "Felis catus", "Canis familiaris", "Bos taurus",
    "Equus caballus", "Ovis aries", "Capra hircus",
}
TOP_N = 12
MIN_ARRAYS = 5
MIN_SITE_YEARS = 10
MIN_CELLS = 12
MIN_SHARED_GRID_CELLS = 2
REQUIRED_DEP = {
    "Deployment_ID", "Camera_Trap_Array", "Site_Name", "Development_Level",
    "Latitude", "Longitude", "Start_Date", "End_Date",
}
REQUIRED_SEQ = {
    "Deployment_ID", "Sequence_ID", "Start_Time", "Class", "Genus", "Species",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()


def verify(path: Path, expected: str) -> None:
    if sha256(path) != expected:
        raise ValueError("E6 pinned Dryad file hash mismatch: " + path.name)


def scientific_name(genus: str, species: str) -> str | None:
    genus, species = genus.strip(), species.strip()
    if not re.fullmatch(r"[A-Z][a-z]+", genus):
        return None
    if not re.fullmatch(r"[a-z]+", species):
        return None
    name = genus + " " + species
    return None if name in EXCLUDED_TAXA else name


def recorded_clock_bin(ts: datetime) -> str | None:
    h = ts.hour
    if h >= 21 or h < 4:
        return "night"
    if 10 <= h < 16:
        return "midday"
    return None


def fixed_geography(lat: float, lon: float) -> tuple[int, int]:
    return (math.floor(lat / 5.0), math.floor(lon / 10.0))


def _date(v: str) -> date:
    return date.fromisoformat(str(v).strip()[:10])


def load_deployments(path: Path, cohort: str) -> tuple[dict, dict]:
    verify(path, DATA[cohort]["deployment_sha256"])
    seen, ambiguous = {}, set()
    array_dev = defaultdict(set)
    site_geo = defaultdict(set)
    qc = Counter()
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not REQUIRED_DEP <= set(reader.fieldnames or ()):
            raise ValueError("missing SNAPSHOT USA deployment metadata columns")
        for row in reader:
            qc["input_rows"] += 1
            dep = str(row["Deployment_ID"]).strip()
            arr = str(row["Camera_Trap_Array"]).strip()
            site = str(row["Site_Name"]).strip()
            dev = str(row["Development_Level"]).strip().lower()
            if not dep or not arr or not site or dev not in LOW | HIGH:
                qc["invalid_site_or_development"] += 1
                continue
            try:
                start, end = _date(row["Start_Date"]), _date(row["End_Date"])
                year = int(float(row["Year"])) if str(row.get("Year", "")).strip() else start.year
                lat, lon = float(row["Latitude"]), float(row["Longitude"])
                if end <= start or not math.isfinite(lat) or not math.isfinite(lon):
                    raise ValueError("bad date or geography")
                if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                    raise ValueError("bad geography")
            except (ValueError, TypeError, OverflowError):
                qc["invalid_deployment_date_or_coordinate"] += 1
                continue
            if (cohort == "history" and year not in (2019, 2020, 2021, 2022, 2023)) or (
                cohort == "holdout_2024" and year != 2024
            ):
                qc["wrong_year_partition"] += 1
                continue
            if end < date(year, 9, 1) or start > date(year, 10, 31):
                qc["outside_frozen_september_october"] += 1
                continue
            signature = (year, arr, site, dev, lat, lon, start, end)
            if dep in seen and seen[dep] != signature:
                ambiguous.add(dep)
            else:
                seen[dep] = signature
            array_dev[arr].add(dev)
            site_geo[(year, arr, site)].add((round(lat, 4), round(lon, 4)))
    conflicting_arrays = {a for a, values in array_dev.items() if len(values) > 1}
    conflicting_sites = {site for site, values in site_geo.items() if len(values) > 1}
    source = {}
    for dep, record in seen.items():
        year, arr, site, dev, lat, lon, start, end = record
        if dep in ambiguous or arr in conflicting_arrays or (year, arr, site) in conflicting_sites:
            qc["conflicted_deployment_or_array_site"] += 1
            continue
        group = "low" if dev in LOW else "high"
        source[dep] = {
            "year": year, "array": arr, "site": (year, arr, site),
            "group": group, "development": dev,
            "grid": fixed_geography(lat, lon),
            "start": start, "end": end,
        }
        qc["eligible_deployments"] += 1
        qc["eligible_" + group] += 1
    qc["conflicting_array_names"] = len(conflicting_arrays)
    qc["conflicting_physical_site_names"] = len(conflicting_sites)
    qc["conflicting_deployment_ids"] = len(ambiguous)
    if not source:
        raise ValueError("zero source-qualified deployment records")
    return source, dict(qc)


def load_events(path: Path, cohort: str, deployments: dict) -> tuple[dict, dict, dict]:
    verify(path, DATA[cohort]["sequence_sha256"])
    counts = defaultdict(lambda: defaultdict(Counter))
    occupancy = defaultdict(set)
    species_sites = defaultdict(set)
    qc = Counter()
    seen = set()
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not REQUIRED_SEQ <= set(reader.fieldnames or ()):
            raise ValueError("missing SNAPSHOT USA sequence headers")
        for row in reader:
            qc["source_sequence_rows"] += 1
            dep = str(row["Deployment_ID"]).strip()
            if dep not in deployments:
                qc["unlinked_deployment"] += 1
                continue
            if str(row["Class"]).strip().lower() != "mammalia":
                qc["not_mammalia_or_unknown"] += 1
                continue
            name = scientific_name(str(row["Genus"]), str(row["Species"]))
            if name is None:
                qc["invalid_or_excluded_taxon"] += 1
                continue
            seq = str(row["Sequence_ID"]).strip()
            if not seq:
                qc["missing_sequence_identity"] += 1
                continue
            try:
                timestamp = datetime.fromisoformat(str(row["Start_Time"]).strip().replace("Z", "+00:00"))
            except ValueError:
                qc["invalid_sequence_time"] += 1
                continue
            metadata = deployments[dep]
            if timestamp.year != metadata["year"] or timestamp.month not in (9, 10):
                qc["outside_frozen_year_or_season"] += 1
                continue
            if not (metadata["start"] <= timestamp.date() <= metadata["end"]):
                qc["outside_deployment_dates"] += 1
                continue
            key = dep, seq, name
            if key in seen:
                qc["duplicate_sequence_species"] += 1
                continue
            seen.add(key)
            occupancy[name].add((metadata["array"], metadata["year"]))
            species_sites[name].add(metadata["site"])
            qc["valid_unique_mammal_sequences"] += 1
            diel = recorded_clock_bin(timestamp)
            if diel is None:
                qc["twilight_or_nonfocal_hour_excluded"] += 1
                continue
            counts[metadata["site"]][name][diel] += 1
            qc["night" if diel == "night" else "midday"] += 1
    return counts, occupancy, {**qc, "distinct_retained_taxa": len(occupancy), "taxa_sites": {s:len(v) for s,v in species_sites.items()}}


def fixed_top_taxa(occupancy: dict, site_counts: dict) -> list[str]:
    """Ranks by historical array-year frequency, then site-year, then name."""
    site_presence = Counter()
    for site, species in site_counts.items():
        for name in species:
            site_presence[name] += 1
    ranked = sorted(
        occupancy, key=lambda name: (-len(occupancy[name]), -site_presence[name], name)
    )
    return ranked[:TOP_N]


def site_mh_for_pair(
    site_counts: dict,
    metadata_by_site: dict,
    species1: str, species2: str,
    *,
    allowed_grids: set | None = None,
) -> dict:
    by_group = {"low": defaultdict(lambda: [0.0, 0.0, 0]),
                "high": defaultdict(lambda: [0.0, 0.0, 0])}
    for site, taxa in site_counts.items():
        meta = metadata_by_site[site]
        if allowed_grids is not None and meta["grid"] not in allowed_grids:
            continue
        row1, row2 = taxa.get(species1), taxa.get(species2)
        if not row1 or not row2:
            continue
        a, b = row1["night"], row1["midday"]
        c, d = row2["night"], row2["midday"]
        n = a + b + c + d
        if min(a+b,c+d,a+c,b+d) <= 0:
            continue
        group, arr = meta["group"], meta["array"]
        score = by_group[group][arr]
        score[0] += a*d/n
        score[1] += b*c/n
        score[2] += 1
    groups = {g: calculate_group(by_group[g]) for g in ("low", "high")}
    lo, hi = groups["low"], groups["high"]
    good = lo["odds"] is not None and hi["odds"] is not None
    ratio = hi["odds"] / lo["odds"] if good else None
    return {
        "species1": species1, "species2": species2, "groups": groups,
        "development_ratio": ratio,
        "log_development_ratio": math.log(ratio) if good else None,
        "species_rank_reversal": bool(
            good and ((lo["odds"] < 1 < hi["odds"]) or (hi["odds"] < 1 < lo["odds"]))
        ),
        "direction_robust_to_array_deletion": (
            bool(good and lo["full_loo"] and hi["full_loo"] and (
                hi["loo_min"]/lo["loo_max"] > 1 or hi["loo_max"]/lo["loo_min"] < 1
            ))
        ),
        "status": "DESCRIPTIVE_COMPARABLE" if good else "INSUFFICIENT_ARRAY_SITE_SUPPORT",
    }


def calculate_group(arrays: dict) -> dict:
    arr_n = len(arrays)
    cell_n = sum(v[2] for v in arrays.values())
    out = {"arrays": arr_n, "informative_site_years": cell_n,
           "status": "INSUFFICIENT_SUPPORT", "odds": None,
           "loo_min": None, "loo_max": None, "full_loo": False}
    if arr_n < MIN_ARRAYS or cell_n < max(MIN_CELLS, MIN_SITE_YEARS):
        return out
    nums = math.fsum(v[0] for v in arrays.values())
    dens = math.fsum(v[1] for v in arrays.values())
    if nums <= 0 or dens <= 0:
        out["status"] = "ZERO_MH_CROSSPRODUCT"
        return out
    out["status"], out["odds"] = "DESCRIPTIVE_ESTIMABLE", nums/dens
    if arr_n <= MIN_ARRAYS:
        return out
    loo = []
    for _, (n, d, count) in arrays.items():
        if arr_n-1 < MIN_ARRAYS or cell_n-count < max(MIN_CELLS, MIN_SITE_YEARS):
            continue
        nn, dd = nums-n, dens-d
        if nn > 0 and dd > 0:
            loo.append(nn/dd)
    if len(loo) == arr_n:
        out["full_loo"] = True
        out["loo_min"], out["loo_max"] = min(loo), max(loo)
    return out


def geometry_overlap(deployments: dict) -> set[tuple[int, int]]:
    groups = defaultdict(set)
    for m in deployments.values():
        groups[m["grid"]].add(m["group"])
    return {grid for grid, labels in groups.items() if len(labels) == 2}


def summarize_pairs(events: dict, source: dict, roster: list[str]) -> dict:
    meta = {}
    for m in source.values():
        site = m["site"]
        if site in meta and any(meta[site][k] != m[k] for k in ("group", "array", "grid")):
            raise ValueError("ambiguous site-year metadata mapping")
        meta[site] = m
    grids = geometry_overlap(source)
    pairs = []
    for sp1, sp2 in combinations(sorted(roster), 2):
        base = site_mh_for_pair(events, meta, sp1, sp2)
        spatial = site_mh_for_pair(events, meta, sp1, sp2, allowed_grids=grids)
        if len(grids) < MIN_SHARED_GRID_CELLS:
            spatial["status"] = "INSUFFICIENT_COMMON_GEOGRAPHY"
            spatial["development_ratio"] = None
            spatial["log_development_ratio"] = None
            spatial["direction_robust_to_array_deletion"] = False
        pairs.append({
            "species1": sp1, "species2": sp2,
            "national": base, "shared_grid": spatial,
        })
    return {
        "fixed_species_pair_count": len(pairs),
        "shared_development_grid_cells": len(grids),
        "national_comparable": sum(x["national"]["status"] == "DESCRIPTIVE_COMPARABLE" for x in pairs),
        "national_rank_reversals": sum(x["national"]["species_rank_reversal"] for x in pairs),
        "national_array_deletion_robust_directions": sum(
            x["national"]["direction_robust_to_array_deletion"] for x in pairs
        ),
        "geographic_sensitivity_comparable": sum(
            x["shared_grid"]["status"] == "DESCRIPTIVE_COMPARABLE" for x in pairs
        ),
        "all_pairs": pairs,
    }


def audit(history_deploy: Path, history_sequences: Path,
          holdout_deploy: Path, holdout_sequences: Path) -> dict:
    hist, hist_meta_qc = load_deployments(history_deploy, "history")
    hold, hold_meta_qc = load_deployments(holdout_deploy, "holdout_2024")
    events_h, occupancy, h_qc = load_events(history_sequences, "history", hist)
    roster = fixed_top_taxa(occupancy, events_h)
    if len(roster) < 2:
        raise ValueError("too few historically supported species to define panel")
    result_h = summarize_pairs(events_h, hist, roster)
    # 2024 response is *only now opened*: cannot influence panel selection.
    events_v, _unused_occupancy, v_qc = load_events(holdout_sequences, "holdout_2024", hold)
    result_v = summarize_pairs(events_v, hold, roster)
    by_pair_h = {
        (p["species1"], p["species2"]): p
        for p in result_h["all_pairs"]
    }
    comparisons = []
    for row in result_v["all_pairs"]:
        pair = row["species1"], row["species2"]
        train, valid = by_pair_h[pair]["national"], row["national"]
        enough = train["status"] == valid["status"] == "DESCRIPTIVE_COMPARABLE"
        direction_agreement = bool(enough and train["log_development_ratio"]*valid["log_development_ratio"] > 0)
        comparisons.append({
            "species1": pair[0], "species2": pair[1],
            "both_years_qualified": enough,
            "historical_log_effect": train["log_development_ratio"],
            "2024_log_effect": valid["log_development_ratio"],
            "same_effect_direction_2024": direction_agreement,
            "historical_array_deletion_robust": train["direction_robust_to_array_deletion"],
            "2024_array_deletion_robust": valid["direction_robust_to_array_deletion"],
            "strict_directionally_robust_both_periods": (
                direction_agreement and train["direction_robust_to_array_deletion"]
                and valid["direction_robust_to_array_deletion"]
            ),
        })
    return {
        "status": "E6_INDEPENDENT_TEMPORAL_HOLDOUT_DESCRIPTIVE_RESULT",
        "frozen_design": "docs/replication/E6_SNAPSHOT_URBAN_TEMPORAL_ASSEMBLY_FROZEN_DESIGN.md",
        "historical_taxon_panel_selected_before_2024_response": roster,
        "input_digest": {k: {name:v for name,v in spec.items()} for k,spec in DATA.items()},
        "qc": {"historical_deployments": hist_meta_qc, "historical_sequences": {k:v for k,v in h_qc.items() if k!="taxa_sites"},
               "holdout_deployments": hold_meta_qc,"holdout_sequences": {k:v for k,v in v_qc.items() if k!="taxa_sites"}},
        "historical": result_h,
        "holdout_2024": result_v,
        "temporal_replication": {
            "both_years_comparable_pairs": sum(p["both_years_qualified"] for p in comparisons),
            "pair_direction_concordance_count": sum(p["same_effect_direction_2024"] for p in comparisons),
            "fully_array_deletion_robust_concordant_pairs": sum(p["strict_directionally_robust_both_periods"] for p in comparisons),
            "all_pairs": comparisons,
        },
        "claims_boundary": {
            "heldout_year_independent_of_training_event_values": True,
            "physical_camera_arrays_may_overlap_across_years": True,
            "hour_bins_are_camera_recorded_civil_clock_not_true_solar_phase": True,
            "urbanization_as_causal_exposure_identified": False,
            "animal_activity_separated_from_camera_detection": False,
            "this_is_a_qualified_E5_replication": False,
            "E5_original_G4_passed": False,
            "E5_original_standard_qualified_candidates": 0,
            "E4_original_scores_changed": False,
            "raw_event_rows_exported": False,
            "formal_inferential_p_values_reported": False,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--historical-deployments", type=Path, required=True)
    p.add_argument("--historical-sequences", type=Path, required=True)
    p.add_argument("--holdout-deployments", type=Path, required=True)
    p.add_argument("--holdout-sequences", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.historical_deployments, args.historical_sequences,
                   args.holdout_deployments, args.holdout_sequences)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "panel": result["historical_taxon_panel_selected_before_2024_response"],
        "historical_comparable": result["historical"]["national_comparable"],
        "2024_comparable": result["holdout_2024"]["national_comparable"],
        "replicated_comparable": result["temporal_replication"]["both_years_comparable_pairs"],
        "direction_concordant": result["temporal_replication"]["pair_direction_concordance_count"],
        "array_loo_robust_both": result["temporal_replication"]["fully_array_deletion_robust_concordant_pairs"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
