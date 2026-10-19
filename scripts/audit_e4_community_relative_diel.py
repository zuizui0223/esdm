#!/usr/bin/env python3
"""Post-outcome, descriptive community-relative diel audit on frozen MICA capture.

This is not a repeat of E4 fitting, E5 calibration, causal behavioral inference
or preregistered selection of taxa. Rattus/Ondatra were chosen after inspecting
the existing cross-taxon descriptive outcome. Only aggregate outputs leave the run.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

from esdm.validate.e2_mica_response_blind import qualify_e2_mica_archive

RAT = "Rattus norvegicus"
MUSKRAT = "Ondatra zibethicus"
SPECIES = (RAT, MUSKRAT)
PINNED_MICA_SHA256 = "8346f3fe467a201525d6bedd4ebd6e2078457ee8bb778501d41d55ace7d962c9"
EXPECTED = {
    "training": {RAT: (4348, 463), MUSKRAT: (1237, 100)},
    "heldout_D": {RAT: (1694, 78), MUSKRAT: (3812, 1279)},
}
MIN_INFORMATIVE_SITES = 3
CONTRACT_STATUS = "FROZEN_POSTRESULT_OUTCOME_SELECTED_DESCRIPTIVE_ONLY"


def _iso(text: str) -> datetime:
    return datetime.fromisoformat(str(text).strip().replace("Z", "+00:00"))


def _member(archive: zipfile.ZipFile, basename: str) -> str:
    matches = [
        path for path in archive.namelist()
        if PurePosixPath(path).name == basename and not path.endswith("/")
    ]
    if len(matches) != 1:
        raise ValueError(f"source must have exactly one {basename}")
    return matches[0]


def _odds_ratio(site: dict[str, int]) -> tuple[float, float] | None:
    """Mantel-Haenszel contributions for rat vs muskrat by night vs day."""
    a, b = site["rat_n"], site["rat_d"]
    c, d = site["mus_n"], site["mus_d"]
    n = a + b + c + d
    if min(a + b, c + d, a + c, b + d) == 0 or n == 0:
        return None
    return a * d / n, b * c / n


def _mh(sites: list[dict[str, int]]) -> float | None:
    contributions = [item for s in sites if (item := _odds_ratio(s)) is not None]
    if len(contributions) < MIN_INFORMATIVE_SITES:
        return None
    numerator = math.fsum(x for x, _ in contributions)
    denominator = math.fsum(y for _, y in contributions)
    if numerator <= 0 or denominator <= 0:
        return None
    return numerator / denominator


def site_summary(sites: dict[str, dict[str, int]]) -> dict:
    """Site-stratified diagnostics without publishing individual location IDs."""
    all_sites = list(sites.values())
    shared = [
        s for s in all_sites
        if s["rat_n"] + s["rat_d"] > 0 and s["mus_n"] + s["mus_d"] > 0
    ]
    informative = [s for s in shared if _odds_ratio(s) is not None]
    estimate = _mh(informative)
    leave_one_out = []
    if estimate is not None and len(informative) > MIN_INFORMATIVE_SITES:
        for i in range(len(informative)):
            value = _mh(informative[:i] + informative[i + 1:])
            if value is not None:
                leave_one_out.append(value)
    return {
        "physical_locations": len(all_sites),
        "locations_with_both_species_recorded": len(shared),
        "locations_informative_for_site_stratified_diel_contrast": len(informative),
        "recorded_rat_events_in_shared_locations": sum(
            s["rat_n"] + s["rat_d"] for s in shared
        ),
        "recorded_muskrat_events_in_shared_locations": sum(
            s["mus_n"] + s["mus_d"] for s in shared
        ),
        "site_stratified_mantel_haenszel_rat_over_muskrat_odds": estimate,
        "site_stratified_status": (
            "DESCRIPTIVE_COMPUTABLE_NO_INDEPENDENT_DETECTION_CONTROL"
            if estimate is not None else "INSUFFICIENT_MATCHED_SITE_IDENTIFICATION"
        ),
        "leave_one_informative_location_out": (
            {
                "valid_contrasts": len(leave_one_out),
                "min": min(leave_one_out) if leave_one_out else None,
                "max": max(leave_one_out) if leave_one_out else None,
            }
        ),
    }


def _relative_odds(counter: dict[str, dict[str, int]]) -> float:
    return (
        counter[RAT]["night"] * counter[MUSKRAT]["day"]
        / (counter[RAT]["day"] * counter[MUSKRAT]["night"])
    )


def build(archive_path: Path, temporal_path: Path, summary_path: Path) -> dict:
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != PINNED_MICA_SHA256:
        raise ValueError("pinned MICA archive SHA256 mismatch")
    qualification = qualify_e2_mica_archive(archive_path)
    if qualification["status"] != "RESPONSE_BLIND_GEOMETRY_HEADER_PASS":
        raise ValueError("MICA geometry source was not qualified")
    manifest = qualification["manifest"]
    roles = {str(k): v for k, v in manifest["training_role_by_deployment"].items()}
    heldout_ids = frozenset(map(str, manifest["heldout_deployment_ids"]))
    train_ids = {
        deployment_id for deployment_id, role in roles.items()
        if role == "state_annotated"
    }
    if len(train_ids) != 266:
        raise ValueError("training annotated cohort changed")
    temporal = json.loads(temporal_path.read_text(encoding="utf-8"))
    if temporal.get("status") != "TEMPORAL_INTEGRITY_PASS":
        raise ValueError("temporal integrity source changed")
    excluded = {
        (str(r["deploymentID"]), str(r["eventID"]))
        for r in temporal["quarantine"]["event_identities"]
    }
    frozen = json.loads(summary_path.read_text(encoding="utf-8"))
    if frozen["status"] != "POSTRESULT_EXPLORATORY_SUPPLEMENT":
        raise ValueError("cross-taxon source is not frozen exploratory receipt")

    with zipfile.ZipFile(archive_path) as archive:
        deployments = list(csv.DictReader(io.StringIO(
            archive.read(_member(archive, "deployments.csv")).decode("utf-8-sig")
        )))
        observations = csv.DictReader(io.StringIO(
            archive.read(_member(archive, "observations.csv")).decode("utf-8-sig")
        ))
        by_deployment = {}
        for r in deployments:
            dep = str(r["deploymentID"]).strip()
            location = str(r["locationName"]).strip()
            if dep in train_ids:
                cohort = "training"
            elif dep in heldout_ids and location.startswith("D"):
                cohort = "heldout_D"
            else:
                continue
            if not location or dep in by_deployment:
                raise ValueError("physical location/deployment identifier invalid")
            by_deployment[dep] = (cohort, location)
        train_count = sum(value[0] == "training" for value in by_deployment.values())
        heldout_count = sum(value[0] == "heldout_D" for value in by_deployment.values())
        if (train_count, heldout_count) != (266, 164):
            raise ValueError("pinned 266/164 deployment geometry changed")

        counts = {
            cohort: {species: Counter() for species in SPECIES}
            for cohort in ("training", "heldout_D")
        }
        site_counts: dict[str, dict[str, dict[str, int]]] = {
            "training": {}, "heldout_D": {}
        }
        for cohort, location in by_deployment.values():
            site_counts[cohort].setdefault(
                location, dict(rat_n=0, rat_d=0, mus_n=0, mus_d=0)
            )

        seen = set()
        for row in observations:
            if (
                row.get("observationLevel", "").strip() != "event"
                or row.get("observationType", "").strip() != "animal"
            ):
                continue
            dep = str(row.get("deploymentID", "")).strip()
            event = str(row.get("eventID", "")).strip()
            species = str(row.get("scientificName", "")).strip()
            if not event or species not in SPECIES or dep not in by_deployment:
                continue
            if (dep, event) in excluded:
                continue
            key = (dep, event, species)
            if key in seen:
                continue
            seen.add(key)
            diel = "night" if _iso(row["eventStart"]).hour in (*range(0, 6), *range(18, 24)) else "day"
            cohort, location = by_deployment[dep]
            counts[cohort][species][diel] += 1
            suffix = "_n" if diel == "night" else "_d"
            prefix = "rat" if species == RAT else "mus"
            site_counts[cohort][location][prefix + suffix] += 1

    for cohort in counts:
        for species in SPECIES:
            observed = (counts[cohort][species]["night"], counts[cohort][species]["day"])
            if observed != EXPECTED[cohort][species]:
                raise ValueError(f"frozen {cohort}/{species} count mismatch: {observed}")
            row = next(x for x in frozen["taxa"] if x["scientificName"] == species)
            prefix = "training" if cohort == "training" else "heldout_D"
            if observed != (row[prefix + "_night_events"], row[prefix + "_day_events"]):
                raise ValueError("cross-taxon receipt count mismatch")

    global_train = _relative_odds(counts["training"])
    global_d = _relative_odds(counts["heldout_D"])
    summaries = {k: site_summary(v) for k, v in site_counts.items()}
    matched_train = summaries["training"]["site_stratified_mantel_haenszel_rat_over_muskrat_odds"]
    matched_d = summaries["heldout_D"]["site_stratified_mantel_haenszel_rat_over_muskrat_odds"]
    return {
        "status": "POSTRESULT_OUTCOME_SELECTED_COMMUNITY_RELATIVE_DIEL_AUDIT",
        "source": {
            "sha256": PINNED_MICA_SHA256,
            "capture_run_id": 36369531079,
            "prior_cross_taxon_receipt": summary_path.name,
            "frozen_cohort_and_quarantine_reused": True,
        },
        "research_boundary": {
            "species_contrast_chosen_after_prior_result": True,
            "new_model_fit": False,
            "event_level_confidence_interval": False,
            "original_E4_E5_decisions_changed": False,
            "identifies_causal_activity_or_detection": False,
            "raw_site_identifiers_exported": False,
        },
        "aggregate_rat_over_muskrat_night_day_odds": {
            "training": global_train,
            "heldout_D": global_d,
            "ratio_of_ratios": global_d / global_train,
            "log_ratio_of_ratios": math.log(global_d / global_train),
        },
        "shared_site_diagnostic": summaries,
        "site_matched_ratio_of_ratios": (
            matched_d / matched_train
            if matched_train is not None and matched_d is not None
            else None
        ),
        "decision": (
            "SITE_MATCHED_DESCRIPTIVE_ESTIMABLE_NO_CAUSAL_ATTRIBUTION"
            if matched_train is not None and matched_d is not None
            else "SITE_MATCHED_TRANSFER_NOT_ESTIMABLE_WITH_FROZEN_SUPPORT"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--temporal", type=Path, required=True)
    parser.add_argument("--prior-cross-taxon", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.archive, args.temporal, args.prior_cross_taxon)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["decision"],
        "aggregate": result["aggregate_rat_over_muskrat_night_day_odds"],
        "site_matched": result["shared_site_diagnostic"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
