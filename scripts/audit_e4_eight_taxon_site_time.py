#!/usr/bin/env python3
"""Fixed-roster post-outcome eight-taxon camera community diel audit.

Never a new E4 fit, E5 validation, causal activity estimate, or independent
confirmation. The taxa and core question were selected with earlier E4
outcomes already known. The only result exported is an aggregate JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import io
from itertools import combinations
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive

PINNED_CAPTURE_SHA256 = "8346f3fe467a201525d6bedd4ebd6e2078457ee8bb778501d41d55ace7d962c9"
TAXA = (
    "Anas platyrhynchos",
    "Ardea cinerea",
    "Capreolus capreolus",
    "Fulica atra",
    "Gallinula chloropus",
    "Ondatra zibethicus",
    "Rattus norvegicus",
    "Vulpes vulpes",
)
COHORTS = ("training", "heldout_D")
MODE_NAMES = ("site_season", "site_yearmonth")
MIN_SITES = 3
MIN_CELLS = 4
MIN_TIME_BINS = 2


def verify_sha256(path: Path, expected: str = PINNED_CAPTURE_SHA256) -> None:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError("immutable MICA archive SHA256 mismatch")


def archive_member(zf: zipfile.ZipFile, filename: str) -> str:
    names = [p for p in zf.namelist() if PurePosixPath(p).name == filename
             and not p.endswith("/")]
    if len(names) != 1:
        raise ValueError(f"expected exactly one {filename} in frozen archive")
    return names[0]


def parse_date(text: str) -> datetime:
    return datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))


def temporal_bin(date: datetime, mode: str) -> str:
    if mode == "site_yearmonth":
        return f"{date.year:04d}-{date.month:02d}"
    if mode != "site_season":
        raise ValueError("invalid temporal grouping")
    month = date.month
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def cell_rows(
    cells: dict[tuple[str, str], Counter],
    species1: str,
    species2: str,
) -> list[tuple[str, str, int, int, int, int]]:
    """Only informative same-camera same-temporal-bin 2x2 event tables."""
    out = []
    for (location, period), cnt in sorted(cells.items()):
        a, b = cnt[(species1, "night")], cnt[(species1, "day")]
        c, d = cnt[(species2, "night")], cnt[(species2, "day")]
        if min(a + b, c + d, a + c, b + d) > 0:
            out.append((location, period, a, b, c, d))
    return out


def estimate_mh(
    rows: list[tuple[str, str, int, int, int, int]],
    *,
    min_sites: int = MIN_SITES,
    min_cells: int = MIN_CELLS,
    min_time_bins: int = MIN_TIME_BINS,
) -> dict:
    """Descriptive site×time stratification: no event-level uncertainty."""
    sites = {row[0] for row in rows}
    periods = {row[1] for row in rows}
    info = {
        "informative_site_time_cells": len(rows),
        "informative_physical_sites": len(sites),
        "informative_time_bins": len(periods),
    }
    if (len(sites) < min_sites or len(rows) < min_cells
            or len(periods) < min_time_bins):
        return {**info, "status": "INSUFFICIENT_SITE_TIME_SUPPORT", "odds_ratio": None}
    numerator = math.fsum(a*d/(a+b+c+d) for _, _, a, b, c, d in rows)
    denominator = math.fsum(b*c/(a+b+c+d) for _, _, a, b, c, d in rows)
    if numerator <= 0 or denominator <= 0:
        return {**info, "status": "ZERO_MH_CROSSPRODUCT", "odds_ratio": None}
    return {**info, "status": "DESCRIPTIVE_ESTIMABLE", "odds_ratio": numerator / denominator}


def pair_in_cohort(
    cells: dict[tuple[str, str], Counter],
    first: str,
    second: str,
) -> dict:
    rows = cell_rows(cells, first, second)
    out = estimate_mh(rows)
    leave_one = []
    if out["status"] == "DESCRIPTIVE_ESTIMABLE" and out["informative_physical_sites"] >= MIN_SITES + 1:
        for location in sorted({x[0] for x in rows}):
            remaining = [x for x in rows if x[0] != location]
            value = estimate_mh(
                remaining,
                min_sites=MIN_SITES,
                min_cells=MIN_CELLS,
                min_time_bins=MIN_TIME_BINS,
            )
            if value["odds_ratio"] is not None:
                leave_one.append(value["odds_ratio"])
    out["leave_one_physical_site_out"] = {
        "calculable": len(leave_one),
        "minimum": min(leave_one) if leave_one else None,
        "maximum": max(leave_one) if leave_one else None,
    }
    return out


def pair_summary(grouped: dict[str, dict[tuple[str, str], Counter]]) -> dict:
    pairs = []
    for sp1, sp2 in combinations(TAXA, 2):
        train = pair_in_cohort(grouped["training"], sp1, sp2)
        east = pair_in_cohort(grouped["heldout_D"], sp1, sp2)
        enough = (
            train["odds_ratio"] is not None
            and east["odds_ratio"] is not None
        )
        ratio = east["odds_ratio"] / train["odds_ratio"] if enough else None
        reverse = bool(
            enough
            and ((train["odds_ratio"] < 1 < east["odds_ratio"])
                 or (east["odds_ratio"] < 1 < train["odds_ratio"]))
        )
        tr_loo, ea_loo = train["leave_one_physical_site_out"], east["leave_one_physical_site_out"]
        guarded_reverse = bool(
            reverse
            and tr_loo["minimum"] is not None
            and ea_loo["minimum"] is not None
            and ((tr_loo["maximum"] < 1 < ea_loo["minimum"])
                 or (ea_loo["maximum"] < 1 < tr_loo["minimum"]))
        )
        pairs.append({
            "species_1": sp1,
            "species_2": sp2,
            "training": train,
            "heldout_D": east,
            "domain_relative_species1_vs_species2_diel_odds": ratio,
            "observed_rank_reversal": reverse,
            "reversal_survives_all_computable_single_site_deletions": guarded_reverse,
            "decision": "DESCRIPTIVE_PAIR_COMPARABLE" if enough else "PAIR_NOT_COMPARABLE",
        })
    rodent = next(
        x for x in pairs
        if {x["species_1"], x["species_2"]}
        == {"Ondatra zibethicus", "Rattus norvegicus"}
    )
    train = rodent["training"]["odds_ratio"]
    east = rodent["heldout_D"]["odds_ratio"]
    return {
        "fixed_pair_universe": len(pairs),
        "comparable_pairs": sum(p["decision"] == "DESCRIPTIVE_PAIR_COMPARABLE" for p in pairs),
        "pairs_with_observed_rank_reversal": sum(p["observed_rank_reversal"] for p in pairs),
        "reversals_stable_under_all_computable_leave_one_site_out": sum(
            p["reversal_survives_all_computable_single_site_deletions"] for p in pairs
        ),
        "rodent_rat_over_muskrat": {
            "training_odds": 1/train if train is not None else None,
            "heldout_D_odds": 1/east if east is not None else None,
            "relative_change": train/east if train is not None and east is not None else None,
            "rank_reversal": rodent["observed_rank_reversal"],
            "reversal_survives_site_deletions": rodent["reversal_survives_all_computable_single_site_deletions"],
        },
        "all_28_pairs_in_fixed_taxonomic_order": pairs,
    }


def audit(archive: Path, temporal_receipt: Path, prior_receipt: Path) -> dict:
    verify_sha256(archive)
    qualification = qualify_e2_mica_archive(archive)
    if qualification.get("status") != "RESPONSE_BLIND_GEOMETRY_HEADER_PASS":
        raise ValueError("frozen source qualification failed")
    manifest = qualification["manifest"]
    roles = {str(k): str(v) for k, v in manifest["training_role_by_deployment"].items()}
    heldout = set(map(str, manifest["heldout_deployment_ids"]))
    training = {k for k, v in roles.items() if v == "state_annotated"}
    if len(training) != 266:
        raise ValueError("training cohort drift")
    temporal = json.loads(temporal_receipt.read_text(encoding="utf-8"))
    if temporal.get("status") != "TEMPORAL_INTEGRITY_PASS":
        raise ValueError("temporal quarantine not verified")
    quarantine = {(str(x["deploymentID"]), str(x["eventID"]))
                  for x in temporal["quarantine"]["event_identities"]}
    prior = json.loads(prior_receipt.read_text(encoding="utf-8"))
    if (prior.get("status") != "POSTRESULT_EXPLORATORY_SUPPLEMENT"
        or tuple(sorted(x["scientificName"] for x in prior["taxa"])) != TAXA
        or len(prior["taxa"]) != 8):
        raise ValueError("frozen eight-taxon roster changed")
    expected = {
        (cohort, row["scientificName"], diel):
            int(row[("training" if cohort == "training" else "heldout_D") + f"_{diel}_events"])
        for cohort in COHORTS for row in prior["taxa"] for diel in ("night", "day")
    }

    grouped = {mode: {cohort: defaultdict(Counter) for cohort in COHORTS}
               for mode in MODE_NAMES}
    totals = Counter()
    with zipfile.ZipFile(archive) as zf:
        with zf.open(archive_member(zf, "deployments.csv")) as f:
            deployments = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))
        sources = {}
        location_names = {c: set() for c in COHORTS}
        for r in deployments:
            dep, location = str(r["deploymentID"]).strip(), str(r.get("locationName", "")).strip()
            if dep in training:
                cohort = "training"
            elif dep in heldout and location.startswith("D"):
                cohort = "heldout_D"
            else:
                continue
            if not location or dep in sources:
                raise ValueError("ambiguous physical site or deployment")
            sources[dep] = (cohort, location)
            location_names[cohort].add(location)
        if (sum(c == "training" for c, _ in sources.values()),
            sum(c == "heldout_D" for c, _ in sources.values())) != (266, 164):
            raise ValueError("frozen training/heldout geometry mismatch")

        with zf.open(archive_member(zf, "observations.csv")) as f:
            seen = set()
            for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                if row.get("observationLevel", "").strip() != "event" or row.get("observationType", "").strip() != "animal":
                    continue
                dep, eid, name = (str(row.get(field, "")).strip()
                                  for field in ("deploymentID", "eventID", "scientificName"))
                if not eid or dep not in sources or name not in TAXA or (dep, eid) in quarantine:
                    continue
                key = (dep, eid, name)
                if key in seen:
                    continue
                seen.add(key)
                moment = parse_date(row["eventStart"])
                diel = "night" if moment.hour < 6 or moment.hour >= 18 else "day"
                cohort, location = sources[dep]
                totals[(cohort, name, diel)] += 1
                for mode in MODE_NAMES:
                    group = temporal_bin(moment, mode)
                    grouped[mode][cohort][(location, group)][(name, diel)] += 1
    if any(totals[k] != n for k, n in expected.items()):
        raise ValueError("source event counts disagree with original frozen 8-taxon receipt")

    analyses = {mode: pair_summary(grouped[mode]) for mode in MODE_NAMES}
    return {
        "status": "POSTRESULT_OUTCOME_SELECTED_EIGHT_TAXON_COMMUNITY_AUDIT",
        "analysis_date": "2026-10-19",
        "input": {
            "capture_run_id": 36369531079,
            "MICA_source_sha256": PINNED_CAPTURE_SHA256,
            "fixed_taxa": list(TAXA),
            "original_cross_taxon_receipt": prior_receipt.name,
            "original_temporal_quarantine": temporal_receipt.name,
            "training_deployments": 266,
            "heldout_D_deployments": 164,
            "physical_sites": {c: len(location_names[c]) for c in COHORTS},
        },
        "contract": {
            "minimum_distinct_physical_sites": MIN_SITES,
            "minimum_informative_site_time_cells": MIN_CELLS,
            "minimum_distinct_time_bins": MIN_TIME_BINS,
            "site_season": "site × one of four calendar seasons, pooled across years",
            "site_yearmonth": "site × calendar year-month",
            "comparison": "species1 vs species2 night/day Mantel-Haenszel odds",
            "taxon_pairs_complete_not_selected_by_result": True,
            "selected_after_previous_cross_taxon_outcomes": True,
            "new_inferential_CI": False,
        },
        "analyses": analyses,
        "inference_boundary": {
            "source_selected_with_response_previously_exposed": True,
            "all_pairs_reported_including_insufficient_support": True,
            "site_time_stratification_reduces_some_compositional_confounding": True,
            "common_taxon_invariant_observation_multiplier_identified": False,
            "true_animal_activity_identified": False,
            "taxon_specific_observation_unmeasured": True,
            "grouped_sites_cross_geography_match": False,
            "E4_frozen_fit_changed": False,
            "E5_original_G4_passed": False,
            "E5_standard_qualified_count": 0,
            "raw_rows_or_location_names_exported": False,
            "new_model_fit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--prior-eight-taxa", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.archive, args.temporal, args.prior_eight_taxa)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "summary": {
            mode: {
                "comparable_pairs": summary["comparable_pairs"],
                "rank_reversals": summary["pairs_with_observed_rank_reversal"],
                "robust_reversals": summary["reversals_stable_under_all_computable_leave_one_site_out"],
                "rodent": summary["rodent_rat_over_muskrat"],
            }
            for mode, summary in result["analyses"].items()
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
